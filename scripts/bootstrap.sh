#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found. Install Python 3 first."
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "Create .venv"
  python3 -m venv .venv
fi

echo "Upgrade pip/setuptools/wheel"
.venv/bin/python -m pip install --upgrade pip setuptools wheel

echo "Install requirements"
.venv/bin/pip install -r requirements.txt

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

echo "Done. Activate with: source .venv/bin/activate"
