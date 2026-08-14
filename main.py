from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# ─── IMPORT from backend folder ───
try:
    from backend.stock_filter import get_stocks_for_frontend
    print("✅ stock_filter imported from backend folder")
except ImportError as e:
    print(f"❌ Import error: {e}")
    def get_stocks_for_frontend():
        return {
            "timestamp": "2026-01-01T00:00:00",
            "count": 0,
            "data": [],
            "error": f"Import error: {str(e)}"
        }

app = FastAPI()

# ─── CORS ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── STATIC FILES ──────────────────────────────────────
@app.get("/")
async def root():
    return FileResponse("frontend/index.html")

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# ─── API ENDPOINTS ─────────────────────────────────────

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Jarvis Algo API is running"}

@app.get("/api/stocks/all")
async def get_all_stocks():
    """Get all stocks from TradingView"""
    try:
        result = get_stocks_for_frontend()
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "message": "Failed to fetch stocks"}
        )

@app.get("/api/debug")
async def debug_tradingview():
    """Debug endpoint to check if Render can reach TradingView"""
    try:
        import requests
        resp = requests.get("https://www.tradingview.com", timeout=10)
        return {
            "status": "connected",
            "code": resp.status_code,
            "message": "TradingView is reachable"
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
            "message": "Cannot reach TradingView from Render"
        }

@app.get("/api/test-import")
async def test_import():
    """Test if stock_filter is imported correctly"""
    try:
        from backend.stock_filter import get_stocks_for_frontend
        test_result = get_stocks_for_frontend()
        return {
            "status": "success",
            "message": "stock_filter imported and function called",
            "count": test_result.get("count", 0)
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }

# ─── FALLBACK ──────────────────────────────────────────
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    if full_path.startswith("frontend/") or full_path.startswith("static/"):
        return {"message": "Static file"}
    return FileResponse("frontend/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
