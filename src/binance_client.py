import time
import hmac
import hashlib
from urllib.parse import urlencode
import requests

from src.config import BINANCE_API_KEY, BINANCE_API_SECRET, BASE_URL, RECV_WINDOW, DEFAULT_POSITION_SIDE
from src.logger_utils import get_logger
from src.validator import validate_symbol, validate_side, validate_with_filters, validate_positive

logger = get_logger("binance_client")


class BinanceClientError(Exception):
    pass


class BinanceFuturesClient:
    def __init__(self):
        if not BINANCE_API_KEY or not BINANCE_API_SECRET:
            logger.warning("API keys are not set")
        self.api_key = BINANCE_API_KEY
        self.api_secret = BINANCE_API_SECRET.encode("utf-8")

    def _sign(self, params):
        query = urlencode(params, True)
        signature = hmac.new(self.api_secret, query.encode("utf-8"), hashlib.sha256).hexdigest()
        params["signature"] = signature
        return params

    def _headers(self):
        return {"X-MBX-APIKEY": self.api_key}

    def _request(self, method, path, params=None, signed=False):
        if params is None:
            params = {}

        if signed:
            params.setdefault("timestamp", int(time.time() * 1000))
            params.setdefault("recvWindow", RECV_WINDOW)
            params = self._sign(params)

        url = f"{BASE_URL}{path}"

        logger.info(f"HTTP {method} {path}")

        try:
            if method == "GET":
                resp = requests.get(url, headers=self._headers() if signed else None, params=params, timeout=10)
            elif method == "POST":
                resp = requests.post(url, headers=self._headers() if signed else None, params=params, timeout=10)
            elif method == "DELETE":
                resp = requests.delete(url, headers=self._headers() if signed else None, params=params, timeout=10)
            else:
                raise BinanceClientError(f"Unsupported HTTP method {method}")
        except requests.RequestException as exc:
            logger.error(f"Network error: {exc}")
            raise BinanceClientError(f"Network error: {exc}") from exc

        if resp.status_code >= 400:
            try:
                data = resp.json()
            except ValueError:
                data = {"msg": resp.text}
            logger.error(f"API error {resp.status_code}: {data}")
            raise BinanceClientError(f"API error {resp.status_code}: {data}")

        try:
            data = resp.json()
        except ValueError:
            data = resp.text

        logger.info(f"HTTP response OK")
        return data

    def get_exchange_info(self, symbol=None):
        params = {}
        if symbol:
            params["symbol"] = symbol.upper()
        return self._request("GET", "/fapi/v1/exchangeInfo", params=params, signed=False)

    def get_symbol_filters(self, symbol):
        info = self.get_exchange_info(symbol)
        symbol = symbol.upper()
        for s in info.get("symbols", []):
            if s.get("symbol") == symbol:
                return s
        raise BinanceClientError(f"Symbol {symbol} not found")

    def _validate_and_enrich(self, symbol, side, quantity, price=None):
        validate_symbol(symbol)
        validate_side(side)
        validate_positive("quantity", quantity)
        if price is not None:
            validate_positive("price", price)

        symbol_filters = self.get_symbol_filters(symbol)
        filters = symbol_filters.get("filters", [])
        validate_with_filters(symbol, quantity, price, filters)

        return {"symbol_info": symbol_filters}

    def place_market_order(self, symbol, side, quantity, position_side=None, reduce_only=False):
        self._validate_and_enrich(symbol, side, quantity, None)

        params = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": "MARKET",
            "quantity": quantity,
            "reduceOnly": "true" if reduce_only else "false",
        }
        params["positionSide"] = position_side or DEFAULT_POSITION_SIDE

        logger.info("Placing MARKET order")
        return self._request("POST", "/fapi/v1/order", params=params, signed=True)

    def place_limit_order(self, symbol, side, quantity, price, time_in_force="GTC", position_side=None, reduce_only=False):
        self._validate_and_enrich(symbol, side, quantity, price)

        params = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": "LIMIT",
            "timeInForce": time_in_force,
            "quantity": quantity,
            "price": price,
            "reduceOnly": "true" if reduce_only else "false",
        }
        params["positionSide"] = position_side or DEFAULT_POSITION_SIDE

        logger.info("Placing LIMIT order")
        return self._request("POST", "/fapi/v1/order", params=params, signed=True)

    def place_stop_limit_order(self, symbol, side, quantity, stop_price, limit_price, time_in_force="GTC", position_side=None, reduce_only=False):
        self._validate_and_enrich(symbol, side, quantity, limit_price)

        params = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": "STOP",
            "timeInForce": time_in_force,
            "quantity": quantity,
            "price": limit_price,
            "stopPrice": stop_price,
            "reduceOnly": "true" if reduce_only else "false",
        }
        params["positionSide"] = position_side or DEFAULT_POSITION_SIDE

        logger.info("Placing STOP-LIMIT order")
        return self._request("POST", "/fapi/v1/order", params=params, signed=True)

    def cancel_order(self, symbol, order_id=None, client_order_id=None):
        params = {"symbol": symbol.upper()}
        if order_id is not None:
            params["orderId"] = order_id
        elif client_order_id is not None:
            params["origClientOrderId"] = client_order_id
        else:
            raise BinanceClientError("order_id or client_order_id must be provided")

        logger.info("Cancelling order")
        return self._request("DELETE", "/fapi/v1/order", params=params, signed=True)

    def get_order(self, symbol, order_id=None, client_order_id=None):
        params = {"symbol": symbol.upper()}
        if order_id is not None:
            params["orderId"] = order_id
        elif client_order_id is not None:
            params["origClientOrderId"] = client_order_id
        else:
            raise BinanceClientError("order_id or client_order_id must be provided")

        logger.info("Query order")
        return self._request("GET", "/fapi/v1/order", params=params, signed=True)
