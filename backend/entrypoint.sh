#!/bin/bash
set -e

# If the model is not yet trained, run the full seed pipeline
if [ ! -f /app/trained_models/xgboost_v1.pkl ]; then
    echo "============================================"
    echo "  First run detected - running seed pipeline"
    echo "  This will take a few minutes..."
    echo "============================================"
    python -m app.database.seed
    echo "============================================"
    echo "  Seed complete! Starting API server..."
    echo "============================================"
else
    echo "Model already trained, starting API server..."
fi

# Start the FastAPI server
python -m app.main
