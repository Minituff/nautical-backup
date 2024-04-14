from fastapi import FastAPI, Depends
from fastapi.security import HTTPBasic
import uvicorn
import os
from typing import Annotated
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from functools import lru_cache
from contextlib import asynccontextmanager

from app.api.config import Settings
from app.api.authorize import authorize
import app.api.nautical_router as nautical_router
from app.logger import Logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = Logger()
    # Steps that will be performed on startup events only once.
    logger.log_this("Starting API on port 8069...", "INFO")
    yield
    # Steps that will happen on shutdown event
    logger = Logger()
    logger.log_this("Shutting down API...", "INFO")


@lru_cache
def get_settings():
    return Settings()


# Mount the directory containing your static files (HTML, CSS, JS) as a static files route.
script_dir = os.path.dirname(__file__)
static_abs_file_path = os.path.join(script_dir, "static/")

app = FastAPI(
    title="Nautical Backup",
    summary="A simple Docker volume backup tool 🚀",
    version=get_settings().NAUTICAL_VERSION,
    lifespan=lifespan,
)

security = HTTPBasic()

# Import other endpoints
app.include_router(nautical_router.router)

app.mount("/static", StaticFiles(directory=static_abs_file_path, html=True), name="static")


@app.get("/")
async def read_index():
    return FileResponse(f"{static_abs_file_path}/index.html")


@app.get("/health-check")
async def health_check():
    return {"status": "healthy"}


@app.get("/auth")
def auth(username: Annotated[str, Depends(authorize)]):
    return {"username": username}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8069, reload=True, log_level="debug")
