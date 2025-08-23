FROM python:3.10-slim

ENV UV_INSTALL_DIR=/usr/local/bin

# Install curl for installing uv
RUN apt-get update && apt-get install -y curl build-essential && rm -rf /var/lib/apt/lists/*

# Install uv using official script
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:/root/.cargo/bin:${PATH}"

WORKDIR /app

# Copy dependency files first for caching
COPY pyproject.toml uv.lock ./

# Install dependencies into .venv
RUN uv sync --frozen

# Copy the rest of the application code
COPY . .

CMD ["bash"]
