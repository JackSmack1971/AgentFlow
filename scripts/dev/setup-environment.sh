#!/usr/bin/env bash
#
# Script: setup-environment.sh
# Purpose: Set up development environment for AgentFlow
# Usage: ./setup-environment.sh [--production]
# Author: AgentFlow Team
# Version: 1.0.0
# Dependencies: Docker, uv, Node.js 20+

set -euo pipefail

readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" >&2
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

check_dependencies() {
    local deps=("docker" "uv" "node")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_error "Required dependency '$dep' is not installed"
            exit 1
        fi
    done
}

validate_env() {
    if [[ -z "${ENVIRONMENT:-}" ]]; then
        log_error "ENVIRONMENT variable is required"
        exit 1
    fi

    case "${ENVIRONMENT}" in
        development|production) ;;
        *)
            log_error "ENVIRONMENT must be 'development' or 'production'"
            exit 1
            ;;
    esac
}

setup_python() {
    log_info "Setting up Python environment..."
    uv sync
}

setup_node() {
    log_info "Setting up Node environment..."
    npm install
}

setup_docker() {
    log_info "Starting Docker services..."
    docker compose -f docker-compose.dev.yml up -d
}

main() {
    log_info "Starting environment setup..."
    check_dependencies
    validate_env

    setup_python
    setup_node
    setup_docker

    log_info "Environment setup completed successfully"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi

