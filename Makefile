
exec:
	@python3 main.py --config="./configs/basic_sample.yaml"

test:
	@pytest -v ./tests

test_cov:
	@pytest -v ./tests/test_unit \
			--cov=runner \
			--cov-report=term-missing