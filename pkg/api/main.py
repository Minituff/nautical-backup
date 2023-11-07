from typing import Union
from fastapi import FastAPI, HTTPException
import subprocess
from fastapi.responses import PlainTextResponse
import docker_router
import nautical_router
import os

# Read version from environment variable or default to '0.0.0' if not set
NAUTICAL_VERSION = os.getenv('NAUTICAL_VERSION', '0.0.0')

app = FastAPI(
    title="Nautical Backup",
    summary="A simple Docker volume backup tool 🚀",
    version=NAUTICAL_VERSION,
)

app.include_router(docker_router.router)
app.include_router(nautical_router.router)


# Existing endpoints
@app.get("/")
def read_root():
    return {"Hello": "World"}

