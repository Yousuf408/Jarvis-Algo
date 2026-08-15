import time
import threading
import requests
from core.config import TV_SCAN_URL, PRICE_MIN, PRICE_MAX, MARKET_CAP_MIN, GAP_THRESHOLD

_tv_scan_cache = []
_tv_scan_cached_at = 0.0
_tv_scan_lock = threading.Lock()

def fetch_tradingview_stocks() -> list[dict]:
    now = time.time()
    with _tv_scan_lock:
        if _tv_scan_cache and (now - _tv_scan_cached_at) < 600:
            return _tv_scan_cache
    
    payload = {
        "columns": ["name", "close", "change", "gap", "volume", "relative_volume_10d_calc", "market_cap_basic", "sector"],
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
    except Exception:
        with _tv_scan_lock:
            return _tv_scan_cache
    
    rows = []
    for item in body.get("data", []):
        d = item.get("d") or []
        if len(d) < 7: continue
        name = str(d[0] or "").strip().upper()
        close = d[2]
        if not name or not isinstance(close, (int, float)) or close <= 0: continue
        gap = float(d[4]) if isinstance(d[4], (int, float)) else 0.0
        if abs(gap) >= GAP_THRESHOLD: continue
        rows.append({"name": name, "close": float(close), "change": float(d[3]), "gap": gap, "volume": float(d[5]), "relative_volume": float(d[6]), "market_cap_basic": float(d[7]), "sector": str(d[8]) if len(d) > 8 else "N/A"})
    
    with _tv_scan_lock:
        _tv_scan_cache = rows
        _tv_scan_cached_at = time.time()
    return rows
