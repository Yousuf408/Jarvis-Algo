from server.candle_tracker import candle_tracker

def compute_200_ema(symbol: str) -> float | None:
    return candle_tracker.get_200_ema(symbol.upper().replace(".NS", ""))

def compute_200_ema_batch(symbols: list[str]) -> dict:
    return {s: compute_200_ema(s) for s in symbols if s}
