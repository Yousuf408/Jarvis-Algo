from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os

# Import the stock filter function
try:
    from stock_filter import get_stocks_for_frontend
except ImportError:
    # If stock_filter.py is not found, create a fallback
    def get_stocks_for_frontend():
        return {
            "timestamp": "2026-01-01T00:00:00",
            "count": 0,
            "data": [],
            "error": "stock_filter.py not found"
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
# Serve HTML as root
@app.get("/")
async def root():
    return FileResponse("frontend/index.html")

# Serve frontend files
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# Also serve root-level files (if any)
if os.path.exists("style.css"):
    app.mount("/static", StaticFiles(directory="."), name="static")

# ─── API ENDPOINTS ─────────────────────────────────────

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Jarvis Algo API is running"}

@app.get("/api/stocks/all")
async def get_all_stocks():
    """
    Get all stocks that pass the filters:
    - Exchange: NSE
    - Price: 200 to 4000
    - Market Cap: > 41,000 Cr
    - Gap: ≤ 2%
    """
    try:
        result = get_stocks_for_frontend()
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── FALLBACK: Serve index.html for any other route ──
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Serve index.html for any unknown route (SPA support)"""
    # Check if it's a static file request
    if full_path.startswith("frontend/") or full_path.startswith("static/"):
        # Let static file handler take care of it
        return {"message": "Static file"}
    
    # Otherwise serve index.html
    return FileResponse("frontend/index.html")

# ─── RUN (for local testing) ──────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
