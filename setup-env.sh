#!/bin/bash
set -e

# setup-env.sh - Script for setting up the EAModeler environment
# This script ensures the correct virtual environment is used and all dependencies are installed

# Define paths (expand home directory)
VENV_PATH=$(eval echo "~/development/uv/eamodeler")
PROJECT_DIR=$(pwd)

echo "┌─────────────────────────────────────────┐"
echo "│     EAModeler Environment Setup         │"
echo "└─────────────────────────────────────────┘"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_PATH" ]; then
    echo "Creating virtual environment at $VENV_PATH..."
    mkdir -p "$(dirname "$VENV_PATH")"
    uv venv --python 3.12 "$VENV_PATH"
else
    echo "Using existing virtual environment at $VENV_PATH"
fi

# Ensure the virtual environment is properly initialized
if [ ! -f "$VENV_PATH/bin/activate" ]; then
    echo "Virtual environment appears incomplete. Recreating..."
    rm -rf "$VENV_PATH"
    mkdir -p "$(dirname "$VENV_PATH")"
    uv venv --python 3.12 "$VENV_PATH"
fi

# Install project in development mode
echo "Installing project in development mode..."
VIRTUAL_ENV="$VENV_PATH" uv pip install -e .

# Install dev dependencies
echo "Installing development dependencies..."
VIRTUAL_ENV="$VENV_PATH" uv pip install -e ".[dev]"

# Install specific packages directly to ensure they're available
echo "Ensuring core packages are installed..."
VIRTUAL_ENV="$VENV_PATH" uv pip install pandas click pydantic

# Verify installation
echo "Verifying pandas installation..."
VIRTUAL_ENV="$VENV_PATH" uv run python -c "import pandas; print(f'Pandas {pandas.__version__} installed successfully')"

# Create a .env file for uv to detect
cat > .env << EOF
# Environment configuration for EAModeler
UV_VENV_PATH=$VENV_PATH
VIRTUAL_ENV=$VENV_PATH
PATH=$VENV_PATH/bin:\$PATH
PYTHONPATH=$(pwd)
EOF

# Create a run wrapper script for easier execution
cat > run.sh << EOF
#!/bin/bash
# Helper script to run commands with the correct virtual environment
source $VENV_PATH/bin/activate
exec "\$@"
EOF

chmod +x run.sh

echo ""
echo "┌─────────────────────────────────────────┐"
echo "│     Environment Setup Complete!         │"
echo "└─────────────────────────────────────────┘"
echo ""
echo "Environment location: $VENV_PATH"
echo ""
echo "Usage options:"
echo "  1. Activate the environment:"
echo "     source ~/development/uv/eamodeler/bin/activate"
echo ""
echo "  2. Use the run.sh helper script:"
echo "     ./run.sh python generate_interface_docs.py"
echo ""
echo "  3. Run with full path specification:"
echo "     $VENV_PATH/bin/python generate_interface_docs.py"
echo ""
echo "  4. Run CLI commands:"
echo "     ./run.sh eamodeler generate-docs [ARGS]"
echo ""