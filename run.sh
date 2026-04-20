#!/bin/bash
cd "$(dirname "$0")"
echo "Starting Gold Sniper v4..."
pip install yfinance pandas numpy scikit-learn xgboost joblib matplotlib flask flask-socketio eventlet requests Pillow --break-system-packages -q 2>&1 | tail -3
echo "Launching dashboard → http://localhost:5000"
python3 web/app.py
