
exec:
	@python3 main.py --config="./configs/sample.yaml"

test:
	@pytest -v ./tests

test_cov:
	@pytest -v ./tests \
			--cov=runner \
			--cov-report=term-missing 