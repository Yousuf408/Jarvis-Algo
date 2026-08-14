from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# Serve index.html as root
@app.get("/")
async def root():
    return FileResponse("index.html")

# Serve static files (CSS, JS, images, etc.)
app.mount("/static", StaticFiles(directory="."), name="static")
