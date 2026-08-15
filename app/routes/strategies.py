"""
Strategy endpoints - Advance ORB, Big Players, SmartMoney.
"""
from fastapi import APIRouter, HTTPException
import pandas as pd
from typing import Optional

from services.screener import fetch_tradingview_stocks
from services.tv_candles import batch_tv_opening_candles
from services.yahoo_candles import batch_yahoo_orb_data
from services.ema import compute_200_ema_batch
from services.margin import calculate_margin_for_df
from services.strategy import BigPlayersStrategy
from core.constants import *
from core.database import save_top5_strategy
from server.candle_tracker import candle_tracker
from utils.market import resolve_reference_date
from utils.helpers import ws_auto_subscribe

router = APIRouter(tags=["strategies"])

@router.get("/api/strategies/advanceorb")
def get_advance_orb(
    budget: int = 100000,
    parts: int = 4,
    near_high: bool = True,
    above_ema: bool = False,
    inside915: bool = False,
    inside3: bool = False,
    calc_qty: bool = False,
    timeframe: int = 5
):
    # Validation
    if budget <= 0:
        raise HTTPException(400, "budget must be > 0")
    if parts < 1 or parts > 20:
        raise HTTPException(400, "parts must be between 1 and 20")
    if timeframe not in (5, 15):
        raise HTTPException(400, "timeframe must be 5 or 15")
    
    # Step 1: Fetch universe from TradingView
    tv_rows = fetch_tradingview_stocks()
    if not tv_rows:
        # Fallback to watchlist + WebSocket
        # ... (your existing fallback logic)
        pass
    
    df = pd.DataFrame(tv_rows) if tv_rows else pd.DataFrame()
    if df.empty:
        return {"strategy": "advanceorb", "count": 0, "data": [], "message": "No stocks found"}
    
    candidate_symbols = df['name'].dropna().astype(str).tolist()
    
    # Step 2: Yahoo data for filters
    yahoo_open_high = None
    if near_high or above_ema or inside915 or inside3:
        yahoo_open_high = batch_yahoo_orb_data(candidate_symbols, timeframe=timeframe)
    
    # Step 3: Apply filters
    if near_high:
        # Filter near high logic...
        pass
    
    if above_ema:
        # Above EMA filter logic...
        pass
    
    if inside3:
        # 3 candles inside logic...
        pass
    
    # Step 4: TradingView candles (authenticated)
    opening_candle_map = {}
    if candidate_symbols:
        opening_candle_map = batch_tv_opening_candles(candidate_symbols, timeframe=timeframe)
    
    # Step 5: Build results
    # ... (your existing result building logic)
    
    # Step 6: Calculate MaxQty
    if calc_qty:
        calculate_margin_for_df(df, budget, parts)
    
    # Step 7: Save top 5
    try:
        save_top5_strategy("advanceorb", result[:5])
    except Exception:
        pass
    
    # Step 8: Subscribe to WS
    try:
        ws_auto_subscribe([str(e["Symbol"]) for e in result])
    except Exception:
        pass
    
    ref_date, is_live = resolve_reference_date()
    
    return {
        "strategy": "advanceorb",
        "name": "Advance ORB",
        "count": len(result),
        "data": result,
        "columns": ADVANCE_ORB_COLUMNS,
        "conditions": conditions,
        "candle_data_available": bool(opening_candle_map),
        "market_closed": not is_live,
        "reference_date": str(ref_date),
    }

@router.get("/api/strategies/bigplayers")
def get_big_players(budget: int = 100000, parts: int = 4):
    # Big Players logic using watchlist + WebSocket
    # ... (your existing logic)
    pass

@router.get("/api/strategies/advanceorb/refresh")
def refresh_
