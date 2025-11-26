import argparse
import sys
from src.binance_client import BinanceFuturesClient
from src.market_orders import MarketOrder
from src.limit_orders import LimitOrder
from src.advanced.stop_limit import StopLimitOrder
from src.advanced.oco import OCOOrder
from src.advanced.twap import TWAPOrder
from src.advanced.grid_strategy import GridStrategy
from src.logger_utils import get_logger

logger = get_logger("main")


def market_order_command(args):
    handler = MarketOrder()
    response = handler.place_order(args.symbol, args.side, args.quantity, args.reduce_only)
    print_order_response(response, "Market Order")


def limit_order_command(args):
    handler = LimitOrder()
    response = handler.place_order(args.symbol, args.side, args.quantity, args.price, args.time_in_force, args.reduce_only)
    print_order_response(response, "Limit Order")


def stop_limit_command(args):
    handler = StopLimitOrder()
    response = handler.place_order(args.symbol, args.side, args.quantity, args.stop_price, args.limit_price, args.time_in_force, args.reduce_only)
    print_order_response(response, "Stop-Limit Order")


def oco_command(args):
    handler = OCOOrder()
    response = handler.place_order(args.symbol, args.side, args.quantity, args.take_profit_price, args.stop_loss_price, args.stop_limit_price)
    print("OCO Order Placed")
    print(f"Order List ID: {response.get('orderListId')}")
    print(f"Symbol: {response.get('symbol')}")
    print(f"Side: {response.get('side')}")
    print(f"Quantity: {response.get('quantity')}")
    print(f"Orders: {len(response.get('orders', []))}")
    for i, order in enumerate(response.get("orders", []), 1):
        print(f"Order {i}:")
        print(f"  Order ID: {order.get('orderId')}")
        print(f"  Type: {order.get('type')}")
        print(f"  Price: {order.get('price')}")
        if order.get("stopPrice"):
            print(f"  Stop Price: {order.get('stopPrice')}")


def twap_command(args):
    handler = TWAPOrder()
    orders = handler.execute_twap(args.symbol, args.side, args.total_quantity, args.duration_minutes, args.num_slices)
    print(f"TWAP Execution Completed")
    print(f"Total slices: {len(orders)}")
    total_executed = sum(float(o.get("executedQty", 0)) for o in orders)
    print(f"Total quantity: {total_executed}")
    if total_executed > 0:
        avg_price = sum(float(o.get("avgPrice", 0)) * float(o.get("executedQty", 0)) for o in orders if o.get("executedQty", 0) > 0) / total_executed
        print(f"Average price: {avg_price:.2f}")


def grid_command(args):
    if args.action == "create":
        handler = GridStrategy()
        orders = handler.create_grid(args.symbol, args.lower_price, args.upper_price, args.num_grids, args.quantity_per_grid, args.side)
        print(f"Grid Created")
        print(f"Total orders: {len(orders)}")
        buy_count = sum(1 for o in orders if o.get("side") == "BUY")
        sell_count = sum(1 for o in orders if o.get("side") == "SELL")
        print(f"BUY orders: {buy_count}")
        print(f"SELL orders: {sell_count}")
    elif args.action == "status":
        handler = GridStrategy()
        status = handler.get_grid_status(args.symbol)
        print(f"Grid Status for {status['symbol']}")
        print(f"Total open orders: {status['total_open_orders']}")
        print(f"BUY orders: {status['buy_orders']}")
        print(f"SELL orders: {status['sell_orders']}")


def print_order_response(response, order_type):
    print(f"{order_type} Placed")
    print(f"Order ID: {response.get('orderId')}")
    print(f"Symbol: {response.get('symbol')}")
    print(f"Side: {response.get('side')}")
    print(f"Type: {response.get('type')}")
    print(f"Quantity: {response.get('origQty')}")
    if response.get("price"):
        print(f"Price: {response.get('price')}")
    if response.get("stopPrice"):
        print(f"Stop Price: {response.get('stopPrice')}")
    print(f"Status: {response.get('status')}")
    if response.get("executedQty"):
        print(f"Executed Quantity: {response.get('executedQty')}")
    if response.get("avgPrice"):
        print(f"Average Price: {response.get('avgPrice')}")


def main():
    parser = argparse.ArgumentParser(description="Binance Futures Trading Bot")
    subparsers = parser.add_subparsers(dest="command", help="Order type")

    market_parser = subparsers.add_parser("market", help="Place a market order")
    market_parser.add_argument("symbol", help="Trading pair symbol")
    market_parser.add_argument("side", choices=["BUY", "SELL"], help="Order side")
    market_parser.add_argument("quantity", type=float, help="Order quantity")
    market_parser.add_argument("--reduce-only", action="store_true", help="Reduce only order")

    limit_parser = subparsers.add_parser("limit", help="Place a limit order")
    limit_parser.add_argument("symbol", help="Trading pair symbol")
    limit_parser.add_argument("side", choices=["BUY", "SELL"], help="Order side")
    limit_parser.add_argument("quantity", type=float, help="Order quantity")
    limit_parser.add_argument("price", type=float, help="Limit price")
    limit_parser.add_argument("--time-in-force", default="GTC", choices=["GTC", "IOC", "FOK"], help="Time in force")
    limit_parser.add_argument("--reduce-only", action="store_true", help="Reduce only order")

    stop_limit_parser = subparsers.add_parser("stop-limit", help="Place a stop-limit order")
    stop_limit_parser.add_argument("symbol", help="Trading pair symbol")
    stop_limit_parser.add_argument("side", choices=["BUY", "SELL"], help="Order side")
    stop_limit_parser.add_argument("quantity", type=float, help="Order quantity")
    stop_limit_parser.add_argument("stop_price", type=float, help="Stop price")
    stop_limit_parser.add_argument("limit_price", type=float, help="Limit price")
    stop_limit_parser.add_argument("--time-in-force", default="GTC", choices=["GTC", "IOC", "FOK"], help="Time in force")
    stop_limit_parser.add_argument("--reduce-only", action="store_true", help="Reduce only order")

    oco_parser = subparsers.add_parser("oco", help="Place an OCO order")
    oco_parser.add_argument("symbol", help="Trading pair symbol")
    oco_parser.add_argument("side", choices=["BUY", "SELL"], help="Order side")
    oco_parser.add_argument("quantity", type=float, help="Order quantity")
    oco_parser.add_argument("take_profit_price", type=float, help="Take-profit price")
    oco_parser.add_argument("stop_loss_price", type=float, help="Stop-loss price")
    oco_parser.add_argument("--stop-limit-price", type=float, help="Stop-limit price")

    twap_parser = subparsers.add_parser("twap", help="Execute a TWAP order")
    twap_parser.add_argument("symbol", help="Trading pair symbol")
    twap_parser.add_argument("side", choices=["BUY", "SELL"], help="Order side")
    twap_parser.add_argument("total_quantity", type=float, help="Total quantity to execute")
    twap_parser.add_argument("duration_minutes", type=int, help="Duration in minutes")
    twap_parser.add_argument("--num-slices", type=int, default=10, help="Number of slices")

    grid_parser = subparsers.add_parser("grid", help="Grid trading strategy")
    grid_subparsers = grid_parser.add_subparsers(dest="action", help="Grid action")

    grid_create_parser = grid_subparsers.add_parser("create", help="Create a grid")
    grid_create_parser.add_argument("symbol", help="Trading pair symbol")
    grid_create_parser.add_argument("lower_price", type=float, help="Lower price bound")
    grid_create_parser.add_argument("upper_price", type=float, help="Upper price bound")
    grid_create_parser.add_argument("num_grids", type=int, help="Number of grid levels")
    grid_create_parser.add_argument("quantity_per_grid", type=float, help="Quantity per grid")
    grid_create_parser.add_argument("--side", default="BOTH", choices=["BOTH", "BUY", "SELL"], help="Order side")

    grid_status_parser = grid_subparsers.add_parser("status", help="Check grid status")
    grid_status_parser.add_argument("symbol", help="Trading pair symbol")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        client = BinanceFuturesClient()
        if not client.api_key or not client.api_secret:
            print("Error: API credentials not set")
            print("Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables")
            sys.exit(1)

        command_handlers = {
            "market": market_order_command,
            "limit": limit_order_command,
            "stop-limit": stop_limit_command,
            "oco": oco_command,
            "twap": twap_command,
            "grid": grid_command,
        }

        handler = command_handlers.get(args.command)
        if handler:
            handler(args)
        else:
            parser.print_help()
            sys.exit(1)

    except KeyboardInterrupt:
        print("Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"CLI command failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
