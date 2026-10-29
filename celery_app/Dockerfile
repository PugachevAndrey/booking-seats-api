FROM python:3.12-alpine

SHELL ["/bin/sh", "-exc"]

# runtime-библиотеки для Pillow + netcat (вместо apt-get)
RUN apk add --no-cache \
    gcc \
    musl-dev \
    python3-dev \
    jpeg-dev \
    zlib-dev \
    libjpeg-turbo-dev \
    libpng-dev \
    freetype-dev \
    netcat-openbsd

COPY --link --from=ghcr.io/astral-sh/uv:0.4 /uv /usr/local/bin/uv

ARG USER_ID=1000
ARG GROUP_ID=1000

# Alpine: addgroup/adduser (BusyBox), не groupadd/useradd
RUN addgroup -g ${GROUP_ID} devuser \
    && adduser -u ${USER_ID} -G devuser -D -s /bin/sh devuser

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
