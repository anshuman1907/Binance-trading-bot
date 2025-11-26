#!/bin/bash

# Simple test script
export BINANCE_USE_TESTNET=true

python3 -m src.main --help

echo ""
echo "Example commands to trigger orders:"
echo ""
echo "# Market order"
python3 -m src.main market BTCUSDT BUY 0.01
echo ""
echo "# Limit order"
python3 -m src.main limit BTCUSDT BUY 0.01 50000
echo ""
echo "# Stop-limit order"
python3 -m src.main stop-limit BTCUSDT BUY 0.01 51000 50900
echo ""
echo "# OCO order"
python3 -m src.main oco BTCUSDT BUY 0.01 52000 48000
echo ""
echo "# TWAP order"
python3 -m src.main twap BTCUSDT BUY 0.1 60
echo ""
echo "# Grid create"
python3 -m src.main grid create BTCUSDT 48000 52000 10 0.01
echo ""
echo "# Grid status"
python3 -m src.main grid status BTCUSDT
