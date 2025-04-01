@echo off

cd 06-vendoring
python -m venv .venv
call .venv\Scripts\activate
.venv\Scripts\pip install pyodide-build
.venv\Scripts\pyodide venv .venv-pyodide
.venv-pyodide\Scripts\pip install -t src/vendor -r vendor.txt

if not exist src\vendor\* (
  echo Vendoring failed: No files in src/vendor
  exit /b 1
)

wrangler deploy --dry-run

echo Vendoring succeeded, listing files in src/vendor...
tree /f /a src\vendor