import argparse
import time
from ..binance_client import BinanceFuturesClient, BinanceClientError
from ..validator import ValidationError, validate_positive
from ..logger_utils import get_logger

logger = get_logger("twap")


class TWAPOrder:
    def __init__(self, client=None):
        self.client = client or BinanceFuturesClient()

    def execute_twap(self, symbol, side, total_quantity, duration_minutes, num_slices=10):
        validate_positive("total_quantity", total_quantity)
        validate_positive("duration_minutes", duration_minutes)
        validate_positive("num_slices", num_slices)

        qty_per_slice = total_quantity / num_slices
        interval = (duration_minutes * 60) / num_slices

        orders = []
        for i in range(num_slices):
            logger.info(f"TWAP slice {i+1}/{num_slices}")
            res = self.client.place_market_order(
                symbol=symbol,
                side=side,
                quantity=qty_per_slice,
                reduce_only=False,
            )
            orders.append(res)
            if i < num_slices - 1:
                time.sleep(interval)

        logger.info("TWAP completed")
        return orders


def main():
    parser = argparse.ArgumentParser(description="TWAP strategy")
    parser.add_argument("symbol", help="Trading pair")
    parser.add_argument("side", help="BUY or SELL")
    parser.add_argument("total_qty", type=float, help="Total quantity")
    parser.add_argument("duration_sec", type=int, help="Duration in seconds")
    parser.add_argument("slices", type=int, help="Number of slices")
    parser.add_argument("--position-side", default=None, help="BOTH/LONG/SHORT")
    parser.add_argument("--reduce-only", action="store_true", help="Exit only")
    args = parser.parse_args()

    client = BinanceFuturesClient()
    try:
        validate_positive("total_qty", args.total_qty)
        validate_positive("duration_sec", args.duration_sec)
        validate_positive("slices", args.slices)

        qty_per_slice = args.total_qty / args.slices
        interval = args.duration_sec / args.slices

        print(f"TWAP: {args.total_qty} {args.symbol} as {args.slices} slices")

        for i in range(args.slices):
            res = client.place_market_order(
                symbol=args.symbol,
                side=args.side,
                quantity=qty_per_slice,
                position_side=args.position_side,
                reduce_only=args.reduce_only,
            )
            print(f"Slice {i+1}/{args.slices} filled: orderId={res.get('orderId')}")

            if i < args.slices - 1:
                time.sleep(interval)

        print("TWAP complete")

    except (ValidationError, BinanceClientError) as exc:
        logger.error(f"TWAP error: {str(exc)}")
        print(f"Error: {exc}")
    except KeyboardInterrupt:
        print("TWAP interrupted by user")


if __name__ == "__main__":
    main()
