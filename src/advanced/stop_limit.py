import argparse
from ..binance_client import BinanceFuturesClient, BinanceClientError
from ..validator import ValidationError
from ..logger_utils import get_logger

logger = get_logger("stop_limit")


class StopLimitOrder:
    def __init__(self, client=None):
        self.client = client or BinanceFuturesClient()

    def place_order(self, symbol, side, quantity, stop_price, limit_price, time_in_force="GTC", reduce_only=False):
        return self.client.place_stop_limit_order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            stop_price=stop_price,
            limit_price=limit_price,
            time_in_force=time_in_force,
            reduce_only=reduce_only,
        )


def main():
    parser = argparse.ArgumentParser(description="Place STOP-LIMIT order")
    parser.add_argument("symbol", help="Trading pair")
    parser.add_argument("side", help="BUY or SELL")
    parser.add_argument("quantity", type=float, help="Quantity")
    parser.add_argument("stop_price", type=float, help="Stop price")
    parser.add_argument("limit_price", type=float, help="Limit price")
    parser.add_argument("--time-in-force", default="GTC", help="Time in force")
    parser.add_argument("--reduce-only", action="store_true", help="Reduce only")
    parser.add_argument("--position-side", default=None, help="BOTH, LONG or SHORT")
    args = parser.parse_args()

    client = BinanceFuturesClient()
    try:
        res = client.place_stop_limit_order(
            symbol=args.symbol,
            side=args.side,
            quantity=args.quantity,
            stop_price=args.stop_price,
            limit_price=args.limit_price,
            time_in_force=args.time_in_force,
            position_side=args.position_side,
            reduce_only=args.reduce_only,
        )
        print(f"Order placed: {res}")
    except (ValidationError, BinanceClientError) as exc:
        logger.error(f"Failed to place stop-limit order: {str(exc)}")
        print(f"Error: {exc}")


if __name__ == "__main__":
    main()
