"""
Strategy constants - separate from config for clarity.
"""
# ================================================================
# Price & Filtering
# ================================================================
PRICE_MIN = 200
PRICE_MAX = 4000  # 200 to 4000 INR
GAP_THRESHOLD = 2.0  # Absolute gap < 2%
MARKET_CAP_MIN = 41_000_000_000  # 41 Billion INR
SMALL_CANDLE_THRESHOLD = 1.5  # 9:15 candle range <= 1.5%
ABOVE_EMA_MAX_GAP = 3.0  # Max 3% above 200 EMA

# ================================================================
# EMA Configuration
# ================================================================
EMA_SPAN = 200
EMA_LOOKBACK_DAYS = 4

# ================================================================
# Performance
# ================================================================
YFINANCE_WORKERS = 8
MAX_TV_STOCKS = 100

# ================================================================
# Market Hours
# ================================================================
MARKET_OPEN_MIN = 9 * 60 + 15  # 09:15 IST
MARKET_CLOSE_MIN = 15 * 60 + 45  # 15:45 IST
SLOT_LENGTH = 5  # 5-minute slots

# ================================================================
# Auto-Buy Configuration
# ================================================================
AUTO_BUY_CAP = 5
AUTO_BUY_MIN_MOVE_ABOVE_915_PCT = 0.15
AUTO_BUY_MAX_MOVE_ABOVE_915_PCT = 0.50
AUTO_BUY_REQUIRE_PRICE_ABOVE_EMA = True

# ================================================================
# Big Players Auto-Buy
# ================================================================
BP_TRAIL_TRIGGER_PERCENT = 2.0  # Trail SL when price 2% above entry
