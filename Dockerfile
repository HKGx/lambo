FROM python:3.10-slim-buster

RUN apt-get update && apt-get install -y git

RUN pip install poetry

WORKDIR /lambo/

COPY poetry.lock pyproject.toml /lambo/

RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi
RUN poetry run prisma migrate deploy

COPY . /lambo/

CMD [ "poetry", "run", "lambo"]