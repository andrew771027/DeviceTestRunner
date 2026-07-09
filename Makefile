
exec:
	@python3 main.py --config="./configs/sample.yaml"

test:
	@pytest -v ./tests
