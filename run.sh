#!/usr/bin/env bash
# AquaPulse - one-shot setup + run.
set -euo pipefail
cd "$(dirname "$0")"

echo ">> Installing dependencies"
pip install -q -r requirements.txt

echo ">> Running tests"
python -m pytest -q

echo ">> Building the model, factors and dashboard (this trains the global model)"
python src/pipeline.py

echo ">> Starting the API on http://127.0.0.1:8000  (dashboard + live weather + /ask)"
cd src && uvicorn api:app --host 0.0.0.0 --port 8000
