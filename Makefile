start:
	poetry run python -m tg_bot.main

install:
	poetry install

black:
	poetry run black .

pep-isort:
	poetry run isort . 

lint:
	poetry run flake8 tg_bot