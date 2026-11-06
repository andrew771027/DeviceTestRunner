from copy import deepcopy
import pytest
import yaml
from dataclasses import replace
from runner.config_validation import ConfigurationValidationError, validate_schema, validate_cross_fields
from runner.config import ConfigLoader
from runner.models import (
    RunnerConfig,
    DeviceTestCase,
    DeviceInfo,
    LifecycleConfig,
    LifecycleSteps,
    LifecycleStepContent,
    ArtifactConfig,
    ArtifactValidationRule,
    ArtifactValidationConfig,
    RetryConfig,
)

def valid_raw():

    return {
        "test_case": {
            "id": "case",
            "name": "case",
            "description": "test",
        },
        "device":{
            "serial": "${{env.DEVICE_SERIAL}}",
            "product": "pixel",
            "build": "test",
        },
        "variables": {
            "repeat": 3,
            "duration": 5,
        }
        "retry": {
            "max_attempts": 1,
            "delay_seconds": 0,
            "retry_on": [],
        },
        "lifecycle":{
            "scenario": {
                "steps":[
                    {
                        "name": "power",
                        "type": "command",
                        "command": 'echo ${{vars.repeat}}',
                        "timeout_second": "${{vars.duration}}",
                    },
                ], 
            },
        },
        "artifact":{
            "output_dir": "./runs",
            "validation": {
                "rules":[
                    "name": "power_csv",
                    "type": "csv_content",
                    "path": "{{ run.dir }}/result.csv",
                    "after_step": "power",
                    "required_columns": [
                        "voltage",
                    ],
                ],
            },
        },
    }

def config_with_rules(*rules, steps=None):
    return RunnerConfig(
        test_case=DeviceTestCase(id='case', 
                                 name='case', 
                                 description='test',),
        device=DeviceInfo(serial='serial', 
                          product='pixel', 
                          build='build'),
        lifecycle=LifecycleConfig(scenario=LifecycleSteps(steps=steps or [
            LifecycleStepContent(name='power', 
                                type='command', 
                                command='echo ok', 
                                timeout_second=10,),
                                ]
                            )
                        ),
        retry=RetryConfig(max_attempts=1, 
                          retry_on=[],
                        ),
        artifact=ArtifactConfig(output_dir='runs', 
                                ArtifactValidationConfig(list(rules)),
                            ),
        )

def test_valid_schema():
    validate_schema(valid_raw())

@pytest.mark.parameterize(
    "mutate, fragment",
    [
        (lambda x: x['retry'].update(max_attempts=True), 'retry.max_attempts'),
        (lambda x: x['retry'].update(delay_seconds=-1), 'retry.delay_seconds'),
        (lambda x: x['lifecycle']['scenario']['steps'][0].update(timeout_second=0), 'timeout_second'),
        (lambda x: x['lifecycle']['scenario']['steps'][0].update(timeout_second='600'), 'timeout_second'),
        (lambda x: x['artifact']['validation']['rules'][0].update(required='true'), '.required'),
        (lambda x: x['artifact']['validation']['rules'][0].update(min_rows=-1), '.min_rows'),
        (lambda x: x['artifact']['validation']['rules'][0].update(required_columns='voltage'), '.required_columns'),
        (lambda x: x['artifact']['validation']['rules'][0].update(typo='oops'), '.typo'),
        (lambda x: x.update(unknown_root=123), 'root.unknown_root'),
        (lambda x: x.pop('divice'), 'root.device'),
        (lambda x: x['lifecycle']['scenario'].update(steps='not-a-list'), 'steps'),
        (lambda x: x.update(run_timeout_seconds=False), 'run_timeout_seconds'),
        (lambda x: x['variables'].update(repeat=float('int')), 'variables.repeat'),
    ]
)
def test_invalid_schema(mutate, fragment):
    raw = valid_raw()
    mutate(raw)

    with pytest.raises(ConfigurationValidationError, match=fragment):
        validate_schema(raw)

def test_schema_aggregates_multiple_errors():
    raw = valid_raw()
    raw['retry']['max_attempts'] = 0
    raw['artifact']['validation']['rules'][0]['required'] = 'yes'

    with pytest.raises(ConfigurationValidationError) as caught:
        validate_schema(raw)
    
    assert len(caught.value.errors) >= 2

@pytest.mark.parameterize(
    'rule, fragment',
    [
        (ArtifactValidationRule(name='bad', type='exists', path='a', after_step='missing',), 'unknown step',),
        (ArtifactValidationRule(name='bad', type='invalid_type', path='a',), 'unsupported validation type',),
        (ArtifactValidationRule(name='bad', type='file_siza', path='a', min_size_bytes=100, max_size_bytes=10,), 'min_size_bytes',),
        (ArtifactValidationRule(name='bad', type='file_extension', path='a',), 'allowed_extensions',),
        (ArtifactValidationRule(name='bad', type='csv_content', path='a',), 'csv_content requires',),
        (ArtifactValidationRule(name='bad', type='json_content', path='a',), 'json_content requires', ),
    ]
)
def test_invalid_cross_fields(rule, fragment):
    with pytest.raises(ConfigurationValidationError, match=fragment):
        validate_cross_fields(config_with_rules(rule))

def test_duplicate_rule_names_rejected():
    rules = [
        ArtifactValidationRule(name='same', 
                              type='exists',
                              path='a',),
        ArtifactValidationRule(
            name='same',
            type='exists',
            path='a',
        ),
    ]
    
    with pytest.raises(ConfigurationValidationError, match='duplicate artifact rule name'):
        validate_cross_fields(config_with_rules(*rules))

def test_cleanup_after_step_rejected():
    config = config_with_rules(ArtifactValidationRule(name='x', type='exists', path='x', after_step='clean',))
    config = replace(config, lifecycle=replace(config.lifecycle, teardown=LifecycleSteps([
        LifecycleStepContent(name='clean', type='command', command='echo clean', timeout_second=10,)
    ])))
    
    with pytest.raises(ConfigurationValidationError, match='cleanup step'):
        validate_cross_fields(config)

def test_valid_cross_field():
    validate_cross_fields(config_with_rules(ArtifactValidationRule(
        name='power_csv', type='csv_content', path='result.csv', after_step='power', required_columns=['voltage'],
    )))

def test_loader_validates_schema_and_cross_fields(tmp_path):
    raw = valid_raw()

    path = tmp_path / "scenario.yml"

    path.write_text(yaml.safe_dump(raw), encoding='utf-8',)

    config = ConfigLoader().load(str(path))

    assert config.lifecycle.scenario.steps[0].timeout_second == '${{ vars.duration }}'

    raw['artifact']['validation']['rules'][0]['after_step'] == 'missing'

    path.write_text(yaml.safe_dump(raw), encoding='utf-8',)

    with pytest.raises(ConfigurationValidationError, match='unknown step'):
        ConfigLoader().load(str(path))