"""
Centralized configuration module.
All credentials, proxies, URLs, and constants live here.
"""
import os
from pathlib import Path
from zoneinfo import ZoneInfo

# ================================================================
# Paths
# ================================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STOCKS_PATH = PROJECT_ROOT / "stocks" / "watchlist.json"
CANDLES_PATH = PROJECT_ROOT / "stocks" / "candles.json"
CACHE_PATH = PROJECT_ROOT / "stocks" / "strategy_cache.json"
TICKS_PATH = PROJECT_ROOT / "stocks" / "latest_ticks.json"

# ================================================================
# Timezone
# ================================================================
IST = ZoneInfo("Asia/Kolkata")

# ================================================================
# Supabase
# ================================================================
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# ================================================================
# TradingView
# ================================================================
TV_USERNAME = os.getenv("TRADINGVIEW_USERNAME", "")
TV_PASSWORD = os.getenv("TRADINGVIEW_PASSWORD", "")
TV_SCAN_URL = "https://scanner.tradingview.com/india/scan"
TV_SCAN_TTL = 600  # 10 minutes
TV_TOKEN_TTL = 10 * 60  # 10 minutes
TV_LOGIN_COOLDOWN = 5 * 60  # 5 minutes
TV_CANDLE_TTL = 20 * 60 * 60  # 20 hours

# ================================================================
# Proxy Configuration (Shared for all broker calls)
# ================================================================
PROXY_HOST = os.getenv("PROXY_HOST", "151.242.178.149")
PROXY_PORT = os.getenv("PROXY_PORT", "50100")
PROXY_USERNAME = os.getenv("PROXY_USERNAME", "yousufshaikh420")
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD", "cVTbJi6VVA")

PROXY_URL = f"http://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}"
PROXIES = {"http": PROXY_URL, "https": PROXY_URL}

# ================================================================
# Dhan API
# ================================================================
DHAN_BASE_URL = os.getenv("DHAN_API_URL", "https://api.dhan.co")
DHAN_AUTH_URL = os.getenv("DHAN_AUTH_URL", "https://auth.dhan.co")
DHAN_SCRIP_MASTER_URL = "https://images.dhan.co/api-data/api-scrip-master-detailed.csv"
DHAN_ORDER_URL = f"{DHAN_BASE_URL}/v2/orders"
DHAN_MARGIN_URL = f"{DHAN_BASE_URL}/v2/margincalculator"
DHAN_FUND_LIMIT_URL = f"{DHAN_BASE_URL}/v2/fundlimit"
DHAN_HOLDINGS_URL = f"{DHAN_BASE_URL}/v2/holdings"
DHAN_POSITIONS_URL = f"{DHAN_BASE_URL}/v2/positions"

DHAN_TOKEN_TTL = 24 * 3600  # 24 hours
DHAN_AUTO_RENEW_LEAD = 60 * 60  # 1 hour before expiry

# ================================================================
# Angel One API
# ================================================================
ANGEL_BASE_URL = os.getenv("ANGEL_API_URL", "https://apiconnect.angelone.in")
ANGEL_SCRIP_MASTER_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
ANGEL_ORDER_URL = f"{ANGEL_BASE_URL}/rest/secure/angelbroking/order/v1/placeOrder"
ANGEL_ORDER_STATUS_URL = f"{ANGEL_BASE_URL}/rest/secure/angelbroking/order/v1/getOrderBook"
ANGEL_ORDER_CANCEL_URL = f"{ANGEL_BASE_URL}/rest/secure/angelbroking/order/v1/cancelOrder"
ANGEL_ORDER_MODIFY_URL = f"{ANGEL_BASE_URL}/rest/secure/angelbroking/order/v1/modifyOrder"
ANGEL_MARGIN_URL = f"{ANGEL_BASE_URL}/rest/secure/angelbroking/margin/v1/batch"
ANGEL_LOGIN_URL = f"{ANGEL_BASE_URL}/rest/secure/angelbroking/user/v1/loginByClientID"

ANGEL_TOKEN_TTL = 24 * 3600  # 24 hours
ANGEL_AUTO_RENEW_LEAD = 12 * 3600  # 12 hours

# ================================================================
# Dhan WebSocket
# ================================================================
DHAN_FEED_WSS = "wss://api-feed.dhan.co"
REQUEST_QUOTE = 17  # Subscribe to Quote packets
