import sys
from src.binance_client import BinanceFuturesClient
from src.validator import ValidationError
from src.logger_utils import get_logger

logger = get_logger("market_orders")


class MarketOrder:
    def __init__(self, client=None):
        self.client = client or BinanceFuturesClient()

    def place_order(self, symbol, side, quantity, reduce_only=False):
        symbol = symbol.upper().strip()
        side = side.upper().strip()

        logger.info(f"Placing market order: {side} {quantity} {symbol}")

        try:
            response = self.client.place_market_order(symbol=symbol, side=side, quantity=quantity, reduce_only=reduce_only)
            order_id = response.get("orderId")
            logger.info(f"Order placed: {order_id}")
            return response
        except Exception as e:
            logger.error(f"Failed to place market order: {str(e)}")
            raise


def main():
    if len(sys.argv) < 4:
        print("Usage: python -m src.market_orders <SYMBOL> <SIDE> <QUANTITY> [REDUCE_ONLY]")
        sys.exit(1)

    symbol = sys.argv[1]
    side = sys.argv[2]
    quantity = float(sys.argv[3])
    reduce_only = len(sys.argv) > 4 and sys.argv[4].lower() == "true"

    try:
        order_handler = MarketOrder()
        response = order_handler.place_order(symbol, side, quantity, reduce_only)
        print(f"Market Order Placed: {response}")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
