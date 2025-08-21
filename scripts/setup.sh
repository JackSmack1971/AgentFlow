#!/usr/bin/env bash
# scripts/setup.sh - Complete development environment setup

set -euo pipefail

echo "🚀 Setting up AgentFlow development environment..."

# Check dependencies
check_dependency() {
    if ! command -v "$1" &> /dev/null; then
        echo "❌ $1 is required but not installed"
        exit 1
    fi
    echo "✅ $1 found"
}

echo "📋 Checking dependencies..."
check_dependency "python3"
check_dependency "docker"
check_dependency "docker-compose"

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [[ $(echo "$python_version >= 3.10" | bc -l) -eq 0 ]]; then
    echo "❌ Python 3.10+ required, found $python_version"
    exit 1
fi
echo "✅ Python $python_version"

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

# Setup environment file
if [[ ! -f .env ]]; then
    echo "⚙️ Creating .env file from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your API keys and configuration"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
uv install

# Start infrastructure
echo "🐳 Starting infrastructure services..."
./scripts/dev.sh

echo "✅ Development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Run: uvicorn apps.api.app.main:app --reload"
echo "3. Run: python apps/mcp/server.py"
echo ""
echo "API will be available at: http://localhost:8000"
echo "API docs at: http://localhost:8000/docs"
