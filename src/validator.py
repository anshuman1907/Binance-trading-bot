from decimal import Decimal, ROUND_DOWN


class ValidationError(Exception):
    pass


def _decimal(value):
    return Decimal(str(value))


def validate_symbol(symbol):
    if not symbol or not symbol.isalnum():
        raise ValidationError(f"Invalid symbol: {symbol}")


def validate_side(side):
    if side.upper() not in ("BUY", "SELL"):
        raise ValidationError("side must be BUY or SELL")


def validate_positive(name, value):
    d = _decimal(value)
    if d <= 0:
        raise ValidationError(f"{name} must be > 0")


def _apply_step(value, step):
    if step == 0:
        return value
    return (value // step) * step


def validate_with_filters(symbol, quantity, price, filters):
    qty = _decimal(quantity)
    price_dec = _decimal(price) if price is not None else None

    lot_size = next((f for f in filters if f.get("filterType") == "LOT_SIZE"), None)
    price_filter = next((f for f in filters if f.get("filterType") == "PRICE_FILTER"), None)
    min_notional = next((f for f in filters if f.get("filterType") in ("MIN_NOTIONAL", "NOTIONAL")), None)

    if lot_size:
        min_qty = _decimal(lot_size["minQty"])
        step_size = _decimal(lot_size["stepSize"])
        if qty < min_qty:
            raise ValidationError(f"quantity {qty} < minQty {min_qty} for {symbol}")
        if qty != _apply_step(qty, step_size):
            raise ValidationError(f"quantity {qty} is not multiple of stepSize {step_size} for {symbol}")

    if price_filter and price_dec is not None:
        min_price = _decimal(price_filter["minPrice"])
        max_price = _decimal(price_filter["maxPrice"])
        tick_size = _decimal(price_filter["tickSize"])
        if price_dec < min_price or price_dec > max_price:
            raise ValidationError(f"price {price_dec} out of bounds [{min_price}, {max_price}] for {symbol}")
        if price_dec != _apply_step(price_dec, tick_size):
            raise ValidationError(f"price {price_dec} is not multiple of tickSize {tick_size} for {symbol}")

    if min_notional:
        min_not = _decimal(min_notional.get("notional") or min_notional.get("minNotional", "0"))
        if price_dec is not None and min_not > 0:
            notional = qty * price_dec
            if notional < min_not:
                raise ValidationError(f"notional {notional} < minNotional {min_not} for {symbol}")
