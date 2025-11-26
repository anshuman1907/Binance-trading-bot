import argparse
from src.binance_client import BinanceFuturesClient, BinanceClientError
from src.validator import ValidationError
from src.logger_utils import get_logger

logger = get_logger("limit_orders")


class LimitOrder:
    def __init__(self, client=None):
        self.client = client or BinanceFuturesClient()

    def place_order(self, symbol, side, quantity, price, time_in_force="GTC", reduce_only=False):
        symbol = symbol.upper().strip()
        side = side.upper().strip()

        logger.info(f"Placing limit order: {side} {quantity} {symbol} @ {price}")

        try:
            response = self.client.place_limit_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                time_in_force=time_in_force,
                reduce_only=reduce_only,
            )
            logger.info(f"Order placed: {response.get('orderId')}")
            return response
        except Exception as e:
            logger.error(f"Failed to place limit order: {str(e)}")
            raise


def main():
    parser = argparse.ArgumentParser(description="Place Binance Futures LIMIT order")
    parser.add_argument("symbol", help="Trading pair")
    parser.add_argument("side", help="BUY or SELL")
    parser.add_argument("quantity", type=float, help="Quantity")
    parser.add_argument("price", type=float, help="Limit price")
    parser.add_argument("--time-in-force", default="GTC", help="Time in force")
    parser.add_argument("--reduce-only", action="store_true", help="Reduce only")
    parser.add_argument("--position-side", default=None, help="BOTH, LONG or SHORT")
    args = parser.parse_args()

    client = BinanceFuturesClient()
    try:
        res = client.place_limit_order(
            symbol=args.symbol,
            side=args.side,
            quantity=args.quantity,
            price=args.price,
            time_in_force=args.time_in_force,
            position_side=args.position_side,
            reduce_only=args.reduce_only,
        )
        print(f"Order placed: {res}")
    except (ValidationError, BinanceClientError) as exc:
        logger.error(f"Failed to place limit order: {str(exc)}")
        print(f"Error: {exc}")


if __name__ == "__main__":
    main()
