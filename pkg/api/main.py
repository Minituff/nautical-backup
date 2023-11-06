from typing import Union
from fastapi import FastAPI, HTTPException
import subprocess
from fastapi.responses import PlainTextResponse
import docker_router

app = FastAPI()

app.include_router(docker_router.router)


# Existing endpoints
@app.get("/")
def read_root():
    return {"Hello": "World"}

