from fastapi import FastAPI, Depends
from fastapi.security import HTTPBasic
import uvicorn
import os
from typing import Annotated
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from functools import lru_cache

from api.config import Settings
from api.authorize import authorize
import api.nautical_router as nautical_router


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
)

security = HTTPBasic()

# Import other endpoints
app.include_router(nautical_router.router)

app.mount("/static", StaticFiles(directory=static_abs_file_path, html=True), name="static")


@app.get("/")
async def read_index():
    return FileResponse(f"{static_abs_file_path}/index.html")


@app.get("/auth")
def auth(username: Annotated[str, Depends(authorize)]):
    return {"username": username}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8069, reload=True, log_level="debug")
