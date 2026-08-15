"""
TradingView Stock Screener - Fetches NSE stocks with filters.
"""
import time
import threading
import requests

# ================================================================
# CONSTANTS
# ================================================================
PRICE_MIN = 200
PRICE_MAX = 4000
GAP_THRESHOLD = 2.0
MARKET_CAP_MIN = 41_000_000_000  # 41 Billion INR
TV_SCAN_URL = "https://scanner.tradingview.com/india/scan"

# Caching
SCAN_CACHE = []
SCAN_CACHE_TIME = 0.0
SCAN_CACHE_LOCK = threading.Lock()
SCAN_TTL = 600  # 10 minutes

# ================================================================
# SCANNER FUNCTION
# ================================================================

def fetch_tradingview_stocks() -> list[dict]:
    """
    Fetch NSE stocks from TradingView scanner.
    
    Filters: 
        - Exchange: NSE
        - Type: Stock
        - Price: 200 to 4000 INR
        - Market Cap: > 41 Billion INR
    
    Returns: List of dicts with keys: name, close, change, gap, volume, 
             relative_volume, market_cap_basic, sector
    """
    now = time.time()
    with SCAN_CACHE_LOCK:
        if SCAN_CACHE and (now - SCAN_CACHE_TIME) < SCAN_TTL:
            return SCAN_CACHE

    payload = {
        "symbols": {"tickers": [], "query": {"types": []}},
        "columns": [
            "name", "close", "change", "gap", 
            "volume", "relative_volume_10d_calc", "market_cap_basic", "sector"
        ],
        "filter": [
            {"left": "type", "operation": "equal", "right": "stock"},
            {"left": "exchange", "operation": "equal", "right": "NSE"},
            {"left": "close", "operation": "greater", "right": PRICE_MIN},
            {"left": "close", "operation": "less", "right": PRICE_MAX},
            {"left": "market_cap_basic", "operation": "greater", "right": MARKET_CAP_MIN},
        ],
        "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
    }

    try:
        resp = requests.post(TV_SCAN_URL, json=payload, timeout=30)
        resp.raise_for_status()
        body = resp.json()
    except Exception as e:
        print(f"⚠️ TV Scan failed: {e}")
        with SCAN_CACHE_LOCK:
            return SCAN_CACHE

    rows = []
    for item in body.get("data", []):
        d = item.get("d") or []
        if len(d) < 7: 
            continue
        name = str(d[0] or "").strip().upper()
        close = d[2]
        if not name or not isinstance(close, (int, float)) or close <= 0:
            continue
        gap = float(d[4]) if isinstance(d[4], (int, float)) else 0.0
        if abs(gap) >= GAP_THRESHOLD:
            continue
        rows.append({
            "name": name,
            "close": float(close),
            "change": float(d[3]) if isinstance(d[3], (int, float)) else 0.0,
            "gap": gap,
            "volume": float(d[5]) if isinstance(d[5], (int, float)) else 0,
            "relative_volume": float(d[6]) if isinstance(d[6], (int, float)) else 0.0,
            "market_cap_basic": float(d[7]) if len(d) > 7 and isinstance(d[7], (int, float)) else 0,
            "sector": str(d[8]) if len(d) > 8 and d[8] else "N/A",
        })

    with SCAN_CACHE_LOCK:
        SCAN_CACHE = rows
        SCAN_CACHE_TIME = time.time()
    
    return rows
