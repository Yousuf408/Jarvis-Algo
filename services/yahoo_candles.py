"""
Yahoo Finance candle data for ORB filters.
Used by "Near High", "Inside 9:15", and "3 Candles Inside" toggles.
"""
import threading
import time
import pandas as pd
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.config import IST
from core.constants import YFINANCE_WORKERS, EMA_SPAN
from utils.market import resolve_reference_date

# ================================================================
# Per-symbol cache
# ================================================================
_YF_ORB_CACHE: dict[tuple[str, int], tuple[float, dict | None]] = {}
_YF_ORB_CACHE_TTL = 300.0  # 5-min cache for successful fetches
_YF_ORB_FAIL_TTL = 60.0  # 1-min cache for failed fetches
_YF_ORB_LOCK = threading.Lock()

# ================================================================
# Day cache (per trading day)
# ================================================================
_ORB_YAHOO_DAY: dict[tuple[str, int], dict[str, dict | None]] = {}
_ORB_YAHOO_DAY_LOCK = threading.Lock()
_ORB_YAHOO_FETCH_LOCK = threading.Lock()

# ================================================================
# Single-stock fetch
# ================================================================

def fetch_yahoo_orb_data(symbol: str, timeframe: int = 5) -> dict | None:
    """
    Fetch today's opening candle + following candles + yesterday's high.
    
    Returns dict with keys:
      open915, high915, low915, close915, close920 (| None),
      yesterday_high, day_low, near_high_pct, ema200
      plus c2/c3/c4 close/hi/lo
    """
    sym = str(symbol).strip().upper().replace(".NS", "")
    ticker = f"{sym}.NS"
    now = time.time()
    
    with _YF_ORB_LOCK:
        hit = _YF_ORB_CACHE.get((sym, timeframe))
        if hit:
            ttl = _YF_ORB_CACHE_TTL if hit[1] is not None else _YF_ORB_FAIL_TTL
            if now - hit[0] < ttl:
                return hit[1]
    
    try:
        candles = yf.download(
            tickers=ticker,
            period="12d",
            interval=f"{timeframe}m",
            progress=False,
            auto_adjust=False,
            prepost=False,
            threads=False,
        )
    except Exception:
        with _YF_ORB_LOCK:
            _YF_ORB_CACHE[(sym, timeframe)] = (time.time(), None)
        return None
    
    if candles is None or candles.empty:
        with _YF_ORB_LOCK:
            _YF_ORB_CACHE[(sym, timeframe)] = (time.time(), None)
        return None
    
    if isinstance(candles.columns, pd.MultiIndex):
        try:
            candles = candles.xs(ticker, axis=1, level=-1)
        except (KeyError, IndexError):
            try:
                candles = candles.xs(ticker, axis=1, level=0)
            except (KeyError, IndexError):
                return None
    
    for col in ("Open", "High", "Low", "Close"):
        if col not in candles.columns:
            return None
    
    # Convert index to IST
    idx = pd.DatetimeIndex(candles.index)
    if idx.tz is None:
        idx = idx.tz_localize("UTC").tz_convert(IST)
    else:
        idx = idx.tz_convert(IST)
    candles = candles.copy()
    candles.index = idx
    
    # Anchor date
    anchor_date, _ = resolve_reference_date()
    today_rows = candles[candles.index.date == anchor_date]
    
    if today_rows.empty:
        cand_dates = sorted({
            d for d in set(candles.index.date)
            if len(candles[(candles.index.date == d) & (candles.index.hour == 9)
                           & (candles.index.minute >= 15)]) > 0
        }, reverse=True)
        if not cand_dates:
            return None
        anchor_date = cand_dates[0]
        today_rows = candles[candles.index.date == anchor_date]
        if today_rows.empty:
            return None
    
    # 1st candle (9:15)
    opening = today_rows[(today_rows.index.hour == 9) & (today_rows.index.minute >= 15)]
    if opening.empty:
        return None
    c1 = opening.iloc[0]
    high = float(c1["High"])
    low = float(c1["Low"])
    if not high or not low or low <= 0:
        return None
    open_ = float(c1["Open"])
    close = float(c1["Close"])
    
    # 2nd+ candles
    sorted_today = today_rows.sort_index()
    c1_ts = opening.index[0]
    following = sorted_today[sorted_today.index > c1_ts]
    _rows = list(following[["High", "Low", "Close"]].itertuples())
    
    close920 = float(_rows[0].Close) if _rows else None
    
    _next = {}
    for _i, _tag in enumerate(("c2", "c3", "c4"), start=0):
        if len(_rows) > _i:
            _r = _rows[_i]
            _next[f"{_tag}_hi"] = float(_r.High)
            _next[f"{_tag}_lo"] = float(_r.Low)
            _next[f"{_tag}_close"] = float(_r.Close)
        else:
            _next[f"{_tag}_hi"] = None
            _next[f"{_tag}_lo"] = None
            _next[f"{_tag}_close"] = None
    
    # Yesterday's high
    past = candles[candles.index.date < anchor_date]
    yesterday_high = None
    if not past.empty:
        prev_day = max(past.index.date)
        prev_rows = candles[candles.index.date == prev_day]
        if not prev_rows.empty:
            yesterday_high = float(prev_rows["High"].max())
    
    near_high_pct = (
        abs(close - yesterday_high) / yesterday_high * 100
        if yesterday_high and yesterday_high > 0
        else None
    )
    
    # 200-period EMA
    hist = candles[candles.index.date < anchor_date]
    closes = pd.to_numeric(hist["Close"], errors="coerce").dropna()
    ema200 = None
    if len(closes) >= EMA_SPAN:
        ema200 = float(closes.ewm(span=EMA_SPAN, adjust=False).mean().iloc[-1])
    
    result = {
        "timeframe": timeframe,
        "open915": open_,
        "high915": high,
        "low915": low,
        "close915": close,
        "close920": close920,
        "yesterday_high": yesterday_high,
        "day_low": float(today_rows["Low"].min()),
        "near_high_pct": near_high_pct,
        "ema200": ema200,
        "data_date": str(anchor_date),
        "c2_hi": _next.get("c2_hi"), "c2_lo": _next.get("c2_lo"), "c2_close": _next.get("c2_close"),
        "c3_hi": _next.get("c3_hi"), "c3_lo": _next.get("c3_lo"), "c3_close": _next.get("c3_close"),
        "c4_hi": _next.get("c4_hi"), "c4_lo": _next.get("c4_lo"), "c4_close": _next.get("c4_close"),
    }
    
    with _YF_ORB_LOCK:
        _YF_ORB_CACHE[(sym, timeframe)] = (time.time(), result)
    return result

# ================================================================
# Batch fetch (parallel)
# ================================================================

def batch_yahoo_orb_data(symbols: list[str], timeframe: int = 5) -> dict:
    """
    Fetch Yahoo candle data for many symbols in parallel.
    
    Single-flight + per-day cache: completed rows are sealed into the
    day cache so later refreshes re-filter cached rows instead of
    re-downloading the universe.
    """
    unique = [str(s).strip().upper() for s in symbols if s]
    if not unique:
        return {}
    
    _anchor, _ = resolve_reference_date()
    today = _anchor.strftime("%Y-%m-%d")
    cache_key = (today, int(timeframe))
    
    with _ORB_YAHOO_FETCH_LOCK:
        with _ORB_YAHOO_DAY_LOCK:
            day_cache = _ORB_YAHOO_DAY.setdefault(cache_key, {})
            results = {s: day_cache[s] for s in unique if s in day_cache}
            missing = [s for s in unique if s not in day_cache]
        
        if not missing:
            return results
        
        fresh: dict[str, dict | None] = {}
        with ThreadPoolExecutor(max_workers=YFINANCE_WORKERS) as pool:
            futures = {pool.submit(fetch_yahoo_orb_data, sym, int(timeframe)): sym for sym in missing}
            for future in as_completed(futures):
                sym = futures[future]
                try:
                    fresh[sym] = future.result()
                except Exception:
                    fresh[sym] = None
        
        results.update(fresh)
        
        with _ORB_YAHOO_DAY_LOCK:
            day_cache = _ORB_YAHOO_DAY.setdefault(cache_key, {})
            for s, row in fresh.items():
                if row and row.get("close920") is not None:
                    day_cache[s] = row
    
    return results
