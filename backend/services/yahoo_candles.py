import threading
import time
import pandas as pd
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.config import IST
from core.constants import YFINANCE_WORKERS, EMA_SPAN
from utils.market import resolve_reference_date

_YF_ORB_CACHE = {}
_YF_ORB_LOCK = threading.Lock()

def fetch_yahoo_orb_data(symbol: str, timeframe: int = 5) -> dict | None:
    # ... (Your full logic from original common.py)
    pass

def batch_yahoo_orb_data(symbols: list[str], timeframe: int = 5) -> dict:
    # ... (Your full batch logic)
    pass
