FROM python:3.12-slim

SHELL ["/bin/sh", "-exc"]

RUN apt-get update && apt-get upgrade -y && apt-get install --quiet --no-install-recommends --assume-yes netcat-traditional

COPY --link --from=ghcr.io/astral-sh/uv:0.4 /uv /usr/local/bin/uv

ARG USER_ID=1000
ARG GROUP_ID=1000

RUN groupadd -g ${GROUP_ID} devuser \
    && useradd -u ${USER_ID} -g devuser -m -s /bin/bash devuser

USER devuser

ENV UV_PYTHON="python3.12" \
  UV_PYTHON_DOWNLOADS=never \
  UV_LINK_MODE=copy \
  UV_COMPILE_BYTECODE=1 \
  PYTHONOPTIMIZE=1

WORKDIR /app

COPY --chown=$USER_ID:$GROUP_ID pyproject.toml uv.lock /app/

RUN uv sync --no-dev --no-install-project --frozen

ENV PATH=/app/.venv/bin:$PATH \
  PYTHONOPTIMIZE=1 \
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1

COPY --chown=$USER_ID:$GROUP_ID ./shared /app/shared
COPY --chown=$USER_ID:$GROUP_ID ./celery_app /app/celery_app

ENV PYTHONPATH=/app

CMD ["celery", "-A", "celery_app.celery", "worker", "-Q", "notifications,celery", "--loglevel=info"]