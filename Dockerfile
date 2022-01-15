FROM python:3.10-slim-buster

RUN apt-get update && apt-get install -y git

RUN pip install poetry

WORKDIR /lambo/

COPY poetry.lock pyproject.toml /lambo/

RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

COPY . /lambo/

CMD [ "poetry", "run", "lambo"]