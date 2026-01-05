#!/usr/bin/env bash
# POSIX shell script to create a venv and install dependencies.
# Run from the `pro1` directory:
#    ./install_deps.sh

set -euo pipefail

VENV_NAME=${1:-venv}

echo "Creating virtual environment '$VENV_NAME'..."
python -m venv "$VENV_NAME"

echo "Activating virtual environment..."
# shellcheck disable=SC1091
source "$VENV_NAME/bin/activate"

echo "Upgrading pip..."
python -m pip install --upgrade pip

echo "Installing dependencies from requirements.txt..."
if python -m pip install --no-cache-dir -r requirements.txt; then
	echo "Dependencies installed."
else
	echo "pip install failed; purging pip cache and retrying..."
	python -m pip cache purge 2>/dev/null || true
	if python -m pip install --no-cache-dir -r requirements.txt; then
		echo "Dependencies installed after cache purge."
	else
		echo "Retry failed; attempting user install fallback..."
		if python -m pip install --no-cache-dir --user -r requirements.txt; then
			echo "Installed to user site-packages."
		else
			echo "Failed to install dependencies. If you see permission errors, try activating the venv or run with sudo, or run: python -m pip install --user -r requirements.txt" >&2
			exit 2
		fi
	fi
fi

echo "Done. To activate the virtualenv later run: source $VENV_NAME/bin/activate"
