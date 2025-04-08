#!/bin/bash

cd 06-vendoring
python3.12 -m venv .venv
source .venv/bin/activate
.venv/bin/pip install pyodide-build
.venv/bin/pyodide venv .venv-pyodide
.venv-pyodide/bin/pip install -t src/vendor -r vendor.txt

if [ -z "$(ls -A src/vendor)" ]; then
  echo "Vendoring failed: No files in src/vendor"
  exit 1
fi

wrangler deploy --dry-run

echo "Vendoring succeeded, listing files in src/vendor..."
command -v tree &>/dev/null && tree src/vendor || find src/vendor