# backend/stock_filter.py
import requests
import time
import threading
from datetime import datetime
import json

# ─── TradingView Scanner ─────────────────────────────────────
TV_SCAN_URL = "https://scanner.tradingview.com/india/scan"
TV_SCAN_TTL = 600  # 10 minutes cache
_tv_scan_lock = threading.Lock()
_tv_scan_cache = []
_tv_scan_cached_at = 0.0


def fetch_tradingview_stocks():
    """
    Fetch NSE stocks from TradingView scanner with filters:
    - Exchange: NSE
    - Price: 200 to 4000
    - Market Cap: > 41,000 Cr
    - Gap: ≤ 2% (ignored)
    """
    global _tv_scan_cache, _tv_scan_cached_at

    # Check cache first
    now = time.time()
    with _tv_scan_lock:
        if _tv_scan_cache and (now - _tv_scan_cached_at) < TV_SCAN_TTL:
            print(f"📦 Returning cached data ({len(_tv_scan_cache)} stocks)")
            return _tv_scan_cache

    # Build the scan query
    payload = {
        "symbols": {"tickers": [], "query": {"types": []}},
        "columns": [
            "name", "description", "close", "change", "gap",
            "volume", "relative_volume_10d_calc", "market_cap_basic",
            "sector", "open", "high", "low", "change_from_open"
        ],
        "filter": [
            {"left": "type", "operation": "equal", "right": "stock"},
            {"left": "exchange", "operation": "equal", "right": "NSE"},
            {"left": "close", "operation": "greater", "right": 200},
            {"left": "close", "operation": "less", "right": 4000},
            {"left": "market_cap_basic", "operation": "greater", "right": 41000000000},
        ],
        "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
    }

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    }

    try:
        print("🔄 Fetching fresh data from TradingView...")
        resp = requests.post(TV_SCAN_URL, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        body = resp.json()
    except Exception as e:
        print(f"❌ TV scan failed: {e}")
        with _tv_scan_lock:
            return _tv_scan_cache  # Return stale cache

    # Parse results
    rows = []
    for item in body.get("data", []):
        d = item.get("d") or []
        if len(d) < 12:
            continue

        name = str(d[0] or "").strip().upper()
        close = d[2]

        if not name or not isinstance(close, (int, float)) or close <= 0:
            continue

        gap = float(d[4]) if isinstance(d[4], (int, float)) else 0.0

        # Skip gap-up/down beyond 2%
        if abs(gap) >= 2.0:
            continue

        rows.append({
            "name": name,
            "close": float(close),
            "change": float(d[3]) if isinstance(d[3], (int, float)) else 0.0,
            "gap": gap,
            "volume": float(d[5]) if isinstance(d[5], (int, float)) else 0,
            "relative_volume": float(d[6]) if isinstance(d[6], (int, float)) else 0.0,
            "market_cap_basic": float(d[7]) if isinstance(d[7], (int, float)) else 0,
            "sector": str(d[8]) if d[8] else "N/A",
            "open": float(d[9]) if len(d) > 9 and isinstance(d[9], (int, float)) else None,
            "high": float(d[10]) if len(d) > 10 and isinstance(d[10], (int, float)) else None,
            "low": float(d[11]) if len(d) > 11 and isinstance(d[11], (int, float)) else None,
        })

    # Sort by market cap
    rows.sort(key=lambda r: -r["market_cap_basic"])

    # Cache the results
    with _tv_scan_lock:
        _tv_scan_cache = rows
        _tv_scan_cached_at = time.time()

    print(f"✅ Fetched {len(rows)} NSE stocks from TradingView")
    return rows


def get_stocks_for_frontend():
    """Get stocks data formatted for frontend display"""
    stocks = fetch_tradingview_stocks()

    return {
        "timestamp": datetime.now().isoformat(),
        "count": len(stocks),
        "data": [
            {
                "name": s["name"],
                "price": s["close"],
                "change": s["change"],
                "volume": s["volume"]
            }
            for s in stocks
        ]
    }


# ─── For testing ─────────────────────────────────────────────
if __name__ == "__main__":
    # Test the function
    result = get_stocks_for_frontend()
    print(f"\n📊 Total stocks: {result['count']}")
    print(f"⏱  Timestamp: {result['timestamp']}")
    print("\n📋 First 5 stocks:")
    for stock in result['data'][:5]:
        print(f"  {stock['name']}: ₹{stock['price']} ({stock['change']:.2f}%) - Vol: {stock['volume']}")
