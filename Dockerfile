# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.11.8

FROM python:${PYTHON_VERSION}-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential && rm -rf /var/lib/apt/lists/*
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
WORKDIR /app
COPY .python-version pyproject.toml uv.lock ./
RUN test "$PYTHON_VERSION" = "$(cat .python-version)"
RUN uv sync --frozen
COPY . .

FROM python:${PYTHON_VERSION}-slim AS runtime
RUN useradd --create-home appuser
WORKDIR /app
COPY --from=builder /root/.local/bin/uv /usr/local/bin/uv
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"
USER appuser
CMD ["uv", "run", "bash"]
