FROM python:3.14.0-trixie

ENV POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR='/var/cache/pypoetry' \
  POETRY_HOME='/usr/local' \
  POETRY_VERSION=2.1.1\
  PROD=1
RUN curl -sSL https://install.python-poetry.org | python -

WORKDIR /usr/src/app
COPY poetry.lock pyproject.toml ./
RUN poetry install --only=main --no-ansi --no-root
COPY . .
EXPOSE 5001
EXPOSE 1-65535/udp

CMD ["poetry", "run", "hypercorn", "src/s:create_app()", "--bind", "0.0.0.0:5001"]
