#!/bin/bash

BENCHMARK_SCRIPT="benchmark.py"
CONSTRUCT_PACKAGE="construct"


run_benchmark_version() {
    local PY_VERSION=$1
    local VENV_DIR=".venv_py${PY_VERSION}"
    mkdir "$VENV_DIR"

    echo "=========================================================="
    echo "🚀 Starting Benchmark for Python ${PY_VERSION}"
    echo "=========================================================="

    echo "1. Setting up virtual environment..."
    uv venv --python "${PY_VERSION}" --directory "${VENV_DIR}" --clear

    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create venv for Python ${PY_VERSION}. Is that version installed?"
        return 1
    fi

    echo "2. Installing SafeStruct dependencies + construct..."
    source "${VENV_DIR}/bin/activate"

    uv sync --all-groups
    uv pip install ${CONSTRUCT_PACKAGE}

    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies."
        deactivate
        return 1
    fi

    echo "3. Executing benchmark script..."

    python "${BENCHMARK_SCRIPT}"

    deactivate
    echo "4. Deactivating environment."

}

if [ $# -eq 0 ]; then
    echo "Usage: $0 <python-version-1> [python-version-2] ..."
    echo "Example: $0 3.11 3.12 3.13"
    exit 1
fi

echo "--- SafeStruct Cross-Version Benchmarking Initiated ---"

for version in "$@"; do
    run_benchmark_version "$version"
done

echo "--- Benchmarking Complete ---"
