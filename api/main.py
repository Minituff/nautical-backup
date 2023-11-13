from fastapi import FastAPI, HTTPException, APIRouter, Depends, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import uvicorn
import os
import secrets
from typing import Annotated
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from api.authorize import authorize
import api.docker_router as docker_router
import api.nautical_router as nautical_router

# Read version from environment variable or default to '0.0.0' if not set
NAUTICAL_VERSION = os.getenv("NAUTICAL_VERSION", "0.0.0")

# Mount the directory containing your static files (HTML, CSS, JS) as a static files route.
script_dir = os.path.dirname(__file__)
static_abs_file_path = os.path.join(script_dir, "static/")

app = FastAPI(
    title="Nautical Backup",
    summary="A simple Docker volume backup tool 🚀",
    version=NAUTICAL_VERSION,
)

security = HTTPBasic()

# Import other endpoints
app.include_router(docker_router.router)
app.include_router(nautical_router.router)

app.mount("/static", StaticFiles(directory=static_abs_file_path, html=True), name="static")

@app.get("/")
async def read_index():
    return FileResponse(f"{static_abs_file_path}/index.html")

@app.get("/auth")
def auth(username: Annotated[str, Depends(authorize)]):
    return {"Auth granted for username": username}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8069, reload=True, log_level="debug")
