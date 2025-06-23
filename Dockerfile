FROM python:3.12.10-slim

ENV POETRY_VERSION= \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

RUN apt-get update && apt-get install -y curl \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s $POETRY_HOME/bin/poetry /usr/local/bin/poetry \
    && apt-get purge -y --auto-remove curl

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN poetry install

COPY ./src ./src

ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8000"]
