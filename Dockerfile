FROM node:24-slim AS frontend
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
ENV CI="true"
RUN corepack enable
COPY frontend /code/frontend
WORKDIR /code/frontend
RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --frozen-lockfile
RUN pnpm run build

FROM python:3.12 AS backend
ENV POETRY_HOME="/poetry"
ENV POETRY_NO_INTERACTION="1"
ENV POETRY_VIRTUALENVS_IN_PROJECT="true"
ENV PATH="$POETRY_HOME/bin:$PATH"
COPY backend /code/backend
WORKDIR /code/backend
RUN curl -sSL https://install.python-poetry.org | python3 - --version 2.1.1
RUN poetry install --without dev

FROM python:3.12-slim
ENV VIRTUAL_ENV="/code/backend/.venv"
ENV PATH="/code/backend/.venv/bin:$PATH"
COPY --from=frontend /code/frontend/build /code/frontend/build
COPY --from=backend $VIRTUAL_ENV $VIRTUAL_ENV
COPY --from=backend /code/backend /code/backend
COPY db /code/db
WORKDIR /code/backend

ENTRYPOINT PROD=1 hypercorn "src/inter:create_app()" -b 0.0.0.0:5001
