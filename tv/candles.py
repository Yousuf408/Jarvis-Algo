"""
TradingView Authenticated Candle Fetcher - 5m and 15m candles.
"""
import asyncio
import datetime as dt
import json
import os
import random
import re
import string
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import requests
import websockets

# ================================================================
# CONSTANTS
# ================================================================
TV_USERNAME = os.getenv("yousufshaikh420@gmail.com", "")
TV_PASSWORD = os.getenv("Oct9182500100057801", "")

# Caching
TOKEN_CACHE = None
TOKEN_CACHE_TIME = 0.0
TOKEN_TTL = 10 * 60  # 10 minutes
CANDLE_CACHE = {}
CANDLE_LOCK = threading.Lock()
CANDLE_TTL = 20 * 60 * 60  # 20 hours

# ================================================================
# WEBSOCKET HELPERS
# ================================================================

def _frame(method: str, params: List[Any]) -> str:
    payload = json.dumps({"m": method, "p": params}, separators=(",", ":"))
    return f"~m~{len(payload)}~m~{payload}"

def _id(prefix: str) -> str:
    return prefix + "".join(random.choice(string.ascii_lowercase) for _ in range(12))

def _series_rows(raw: str) -> List[List[float]]:
    match = re.search(r'"s":\[(.+?)\}\]', raw, re.S)
    if not match:
        return []
    rows = []
    for item in match.group(1).split(',{"'):
        parts = re.split(r"\[|:|,|\]", item)
        try:
            values = [float(parts[i]) for i in range(4, 10)]
            rows.append(values)
        except (ValueError, IndexError):
            continue
    return rows

def _first_candle(rows: List[List[float]], timeframe: int) -> Tuple[float, float, float, float] | None:
    today = dt.datetime.now().date()
    for row in sorted(rows, key=lambda x: x[0]):
        stamp = dt.datetime.fromtimestamp(row[0])
        if stamp.date() == today and stamp.hour == 9 and stamp.minute == 15:
            return row[1], row[2], row[3], row[4]
    return None

def _yesterday_high(rows: List[List[float]]) -> float | None:
    today = dt.datetime.now().date()
    day_highs = {}
    for row in sorted(rows, key=lambda x: x[0]):
        stamp = dt.datetime.fromtimestamp(row[0])
        if stamp.date() >= today:
            continue
        day_highs[stamp.date()] = max(day_highs.get(stamp.date(), 0.0), row[2])
    if not day_highs:
        return None
    return day_highs[max(day_highs)]

# ================================================================
# ASYNC BATCH FETCH
# ================================================================

async def _batch_fetch_async(
    result: Dict[str, Optional[Tuple[float, float, float, float]]],
    token: str,
    timeframe: int
) -> None:
    chart = _id("cs_")
    async with websockets.connect(
        "wss://data.tradingview.com/socket.io/websocket",
        origin="https://data.tradingview.com",
        ping_interval=None,
        max_size=2**26,
    ) as ws:
        await ws.send(_frame("set_auth_token", [token]))
        await ws.send(_frame("chart_create_session", [chart, ""]))
        
        for index, symbol in enumerate(result):
            tv_symbol = f"NSE:{symbol.removesuffix('.NS')}"
            alias = f"symbol_{index}"
            series = f"s{index}"
            await ws.send(_frame("resolve_symbol", [
                chart, alias,
                f'={{"symbol":"{tv_symbol}","adjustment":"splits","session":"regular"}}',
            ]))
            await ws.send(_frame("create_series", [chart, series, series, alias, f"{timeframe}", 500]))
            
            raw = ""
            while True:
                message = await ws.recv()
                raw += message
                if "series_completed" in message:
                    break
            
            rows = _series_rows(raw)
            candle = _first_candle(rows, timeframe)
            if candle:
                result[symbol] = (*candle, _yesterday_high(rows))

# ================================================================
# PUBLIC API
# ================================================================

def batch_tv_opening_candles(symbols: List[str], timeframe: int = 5) -> Dict[str, Optional[Tuple[float, float, float, float, float | None]]]:
    """
    Fetch 9:15 candle + yesterday's high for multiple symbols.
    
    Args:
        symbols: List of stock symbols
        timeframe: 5 or 15 (minutes)
    
    Returns:
        Dict mapping symbol to tuple (open, high, low, close, yesterday_high)
    """
    result = {s.upper(): None for s in symbols if s}
    timeframe = int(timeframe)

    # Don't fetch before candle closes
    now = dt.datetime.now()
    first_close_min = 9 * 60 + 15 + timeframe
    if now.hour * 60 + now.minute < first_close_min:
        return result

    if not TV_USERNAME or not TV_PASSWORD or not result:
        return result

    today = now.strftime("%Y-%m-%d")
    now_ts = time.time()

    # Check cache
    with CANDLE_LOCK:
        for symbol in list(result):
            cached = CANDLE_CACHE.get((today, timeframe, symbol))
            if cached and now_ts - cached[0] < CANDLE_TTL:
                result[symbol] = cached[1]
        missing = {s: None for s, v in result.items() if v is None}
    
    if not missing:
        return result

    # Get auth token
    token = None
    if TOKEN_CACHE and (now_ts - TOKEN_CACHE_TIME) < TOKEN_TTL:
        token = TOKEN_CACHE
    else:
        try:
            login = requests.post(
                "https://www.tradingview.com/accounts/signin/",
                data={"username": TV_USERNAME, "password": TV_PASSWORD, "remember": "on"},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=20,
            ).json()
            token = (login.get("user") or {}).get("auth_token", "")
            if token:
                TOKEN_CACHE = token
                TOKEN_CACHE_TIME = now_ts
        except Exception as e:
            print(f"⚠️ TV login failed: {e}")
            return result

    if not token:
        return result

    # Fetch candles
    try:
        asyncio.run(_batch_fetch_async(missing, token, timeframe))
        with CANDLE_LOCK:
            for symbol, value in missing.items():
                if value is not None:
                    CANDLE_CACHE[(today, timeframe, symbol)] = (now_ts, value)
                    result[symbol] = value
    except Exception as e:
        print(f"⚠️ TV candle fetch failed: {e}")

    return result
