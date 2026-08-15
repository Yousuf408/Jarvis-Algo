from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uvicorn

# Import the routers
from app.routes import strategies, orders, broker, portfolio, market
from core.config import PROJECT_ROOT
from core.database import ensure_strategy_trades_table

app = FastAPI(
    title="TradeAlgo Pro",
    description="Advance ORB + Big Players Strategy API",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(strategies.router)
app.include_router(orders.router)
app.include_router(broker.router)
app.include_router(portfolio.router)
app.include_router(market.router)

@app.get("/api")
def root():
    return {"status": "ok", "message": "TradeAlgo Pro API"}

@app.get("/api/health")
def health():
    return {"status": "healthy"}

# Static files serving
PROJECT_ROOT = Path(__file__).resolve().parent.parent
app.mount("/js", StaticFiles(directory=PROJECT_ROOT / "frontend/js"), name="frontend-js")
app.mount("/css", StaticFiles(directory=PROJECT_ROOT / "frontend/css"), name="frontend-css")

@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(PROJECT_ROOT / "frontend/index.html", media_type="text/html")

@app.get("/login.html", include_in_schema=False)
def login_page():
    return FileResponse(PROJECT_ROOT / "frontend/login.html", media_type="text/html")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
