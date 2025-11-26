import argparse
import time
from ..binance_client import BinanceFuturesClient, BinanceClientError
from ..validator import ValidationError
from ..logger_utils import get_logger

logger = get_logger("oco")

POLL_INTERVAL = 2.0

def _is_terminal(status):
    return status in ("FILLED", "CANCELED", "EXPIRED", "REJECTED")


class OCOOrder:
    def __init__(self, client=None):
        self.client = client or BinanceFuturesClient()

    def place_order(self, symbol, side, quantity, take_profit_price, stop_loss_price, stop_limit_price=None):
        try:
            tp_res = self.client.place_limit_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=take_profit_price,
                time_in_force="GTC",
                reduce_only=False,
            )
            tp_id = tp_res["orderId"]

            sl_params = {
                "symbol": symbol.upper(),
                "side": side.upper(),
                "type": "STOP_MARKET",
                "stopPrice": stop_loss_price,
                "quantity": quantity,
                "positionSide": "BOTH",
                "reduceOnly": "false",
            }
            if stop_limit_price:
                sl_params["type"] = "STOP"
                sl_params["price"] = stop_limit_price

            sl_res = self.client._request("POST", "/fapi/v1/order", params=sl_params, signed=True)
            sl_id = sl_res["orderId"]

            return {
                "orderListId": f"oco_{tp_id}_{sl_id}",
                "symbol": symbol.upper(),
                "side": side.upper(),
                "quantity": quantity,
                "orders": [
                    {"orderId": tp_id, "type": "LIMIT", "price": take_profit_price},
                    {"orderId": sl_id, "type": sl_params["type"], "stopPrice": stop_loss_price}
                ]
            }
        except (ValidationError, BinanceClientError) as exc:
            logger.error(f"OCO failed: {str(exc)}")
            raise


def main():
    parser = argparse.ArgumentParser(description="OCO order for Binance Futures")
    parser.add_argument("symbol", help="Trading pair")
    parser.add_argument("side", help="BUY or SELL")
    parser.add_argument("quantity", type=float, help="Quantity")
    parser.add_argument("take_profit_price", type=float, help="TP price")
    parser.add_argument("stop_loss_price", type=float, help="SL price")
    parser.add_argument("--position-side", default=None, help="BOTH/LONG/SHORT")
    parser.add_argument("--reduce-only", action="store_true", help="Exit only")
    args = parser.parse_args()

    client = BinanceFuturesClient()
    try:
        tp_res = client.place_limit_order(
            symbol=args.symbol,
            side=args.side,
            quantity=args.quantity,
            price=args.take_profit_price,
            time_in_force="GTC",
            position_side=args.position_side,
            reduce_only=args.reduce_only,
        )
        tp_id = tp_res["orderId"]

        sl_params = {
            "symbol": args.symbol.upper(),
            "side": args.side.upper(),
            "type": "STOP_MARKET",
            "stopPrice": args.stop_loss_price,
            "quantity": args.quantity,
            "positionSide": args.position_side or "BOTH",
            "reduceOnly": "true" if args.reduce_only else "false",
        }
        sl_res = client._request("POST", "/fapi/v1/order", params=sl_params, signed=True)
        sl_id = sl_res["orderId"]

        print(f"OCO created. TP orderId={tp_id}, SL orderId={sl_id}")

        while True:
            time.sleep(POLL_INTERVAL)
            tp = client.get_order(args.symbol, order_id=tp_id)
            sl = client.get_order(args.symbol, order_id=sl_id)
            tp_status = tp.get("status")
            sl_status = sl.get("status")

            if _is_terminal(tp_status) or _is_terminal(sl_status):
                if not _is_terminal(tp_status):
                    client.cancel_order(args.symbol, order_id=tp_id)
                if not _is_terminal(sl_status):
                    client.cancel_order(args.symbol, order_id=sl_id)
                print(f"OCO complete. TP status={tp_status}, SL status={sl_status}")
                break

    except (ValidationError, BinanceClientError) as exc:
        logger.error(f"OCO failed: {str(exc)}")
        print(f"Error: {exc}")


if __name__ == "__main__":
    main()
