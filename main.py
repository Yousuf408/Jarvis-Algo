import sys
import os
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# ================================================================
# 🔥 FIX: Add current directory to Python path
# ================================================================
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ================================================================
# 🔄 IMPORT FROM TV FOLDER (Siblings in root)
# ================================================================
try:
    from tv.screener import fetch_tradingview_stocks
    print("✅ SUCCESS: tv/screener imported correctly")
except ImportError as e:
    print(f"❌ IMPORT ERROR: {e}")
    print("❌ Python cannot find the 'tv' folder. Check your folder structure.")
    def fetch_tradingview_stocks():
        return []

# Wrapper for frontend
def get_stocks_for_frontend():
    try:
        print("🔄 Fetching stocks from TradingView...")
        stocks = fetch_tradingview_stocks()
        print(f"✅ Fetched {len(stocks)} stocks")
        return {
            "timestamp": "2026-01-01T00:00:00",
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
    except Exception as e:
        print("❌ ERROR INSIDE get_stocks_for_frontend:")
        traceback.print_exc()
        return {
            "timestamp": "2026-01-01T00:00:00",
            "count": 0,
            "data": [],
            "error": str(e)
        }

# ================================================================
# APP SETUP
# ================================================================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return FileResponse("frontend/index.html")

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# ================================================================
# API ENDPOINTS
# ================================================================
@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/stocks/all")
async def get_all_stocks():
    try:
        result = get_stocks_for_frontend()
        if "error" in result:
            return JSONResponse(status_code=500, content=result)
        return JSONResponse(content=result)
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

# ================================================================
# RUN
# ================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
