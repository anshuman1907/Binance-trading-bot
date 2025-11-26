import argparse
from ..binance_client import BinanceFuturesClient, BinanceClientError
from ..validator import ValidationError, validate_positive
from ..logger_utils import get_logger

logger = get_logger("grid")


def _build_grid_prices(lower, upper, levels):
    if upper <= lower:
        raise ValidationError("upper_price must be > lower_price")
    if levels < 2:
        raise ValidationError("grid_levels must be >= 2")
    step = (upper - lower) / (levels - 1)
    return [lower + i * step for i in range(levels)]


class GridStrategy:
    def __init__(self, client=None):
        self.client = client or BinanceFuturesClient()

    def create_grid(self, symbol, lower_price, upper_price, num_grids, quantity_per_grid, side="BOTH"):
        validate_positive("quantity_per_grid", quantity_per_grid)
        validate_positive("lower_price", lower_price)
        validate_positive("upper_price", upper_price)
        validate_positive("num_grids", num_grids)

        prices = _build_grid_prices(lower_price, upper_price, num_grids)
        orders = []
        mid_index = len(prices) // 2

        for i, p in enumerate(prices):
            if side == "BUY":
                grid_side = "BUY"
            elif side == "SELL":
                grid_side = "SELL"
            else:
                if i < mid_index:
                    grid_side = "BUY"
                elif i > mid_index:
                    grid_side = "SELL"
                else:
                    continue

            res = self.client.place_limit_order(
                symbol=symbol,
                side=grid_side,
                quantity=quantity_per_grid,
                price=p,
                time_in_force="GTC",
                reduce_only=False,
            )
            orders.append(res)

        return orders

    def get_grid_status(self, symbol):
        all_orders = self.client._request("GET", "/fapi/v1/openOrders", params={"symbol": symbol.upper()}, signed=True)
        buy_count = sum(1 for o in all_orders if o.get("side") == "BUY")
        sell_count = sum(1 for o in all_orders if o.get("side") == "SELL")
        return {
            "symbol": symbol.upper(),
            "total_open_orders": len(all_orders),
            "buy_orders": buy_count,
            "sell_orders": sell_count,
        }


def main():
    parser = argparse.ArgumentParser(description="Grid strategy")
    parser.add_argument("symbol", help="Trading pair")
    parser.add_argument("base_qty", type=float, help="Quantity per order")
    parser.add_argument("lower_price", type=float, help="Lower price")
    parser.add_argument("upper_price", type=float, help="Upper price")
    parser.add_argument("grid_levels", type=int, help="Number of levels")
    parser.add_argument("--mode", default="neutral", choices=["neutral", "long_only"], help="Mode")
    parser.add_argument("--position-side", default=None, help="BOTH/LONG/SHORT")
    parser.add_argument("--reduce-only", action="store_true", help="Exit only")
    args = parser.parse_args()

    client = BinanceFuturesClient()

    try:
        validate_positive("base_qty", args.base_qty)
        validate_positive("lower_price", args.lower_price)
        validate_positive("upper_price", args.upper_price)
        validate_positive("grid_levels", args.grid_levels)

        prices = _build_grid_prices(args.lower_price, args.upper_price, args.grid_levels)
        orders = []
        mid_index = len(prices) // 2

        for i, p in enumerate(prices):
            if args.mode == "long_only":
                side = "BUY"
            else:
                if i < mid_index:
                    side = "BUY"
                elif i > mid_index:
                    side = "SELL"
                else:
                    continue

            res = client.place_limit_order(
                symbol=args.symbol,
                side=side,
                quantity=args.base_qty,
                price=p,
                time_in_force="GTC",
                position_side=args.position_side,
                reduce_only=args.reduce_only,
            )
            orders.append(res)

        print(f"Placed {len(orders)} grid orders")
        for o in orders:
            print(f"  orderId={o.get('orderId')}, side={o.get('side')}, price={o.get('price')}")

    except (ValidationError, BinanceClientError) as exc:
        logger.error(f"Grid error: {str(exc)}")
        print(f"Error: {exc}")


if __name__ == "__main__":
    main()
