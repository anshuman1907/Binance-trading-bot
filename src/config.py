import os


USE_TESTNET = True
BINANCE_API_KEY = "test_api_key"
BINANCE_API_SECRET = "test_api_secret"
BASE_URL = "https://demo-fapi.binance.com" if USE_TESTNET else "https://fapi.binance.com"

RECV_WINDOW = int(os.environ.get("BINANCE_RECV_WINDOW", "5000"))

DEFAULT_POSITION_SIDE = os.environ.get("BINANCE_POSITION_SIDE", "BOTH")  # BOTH/LONG/SHORT
