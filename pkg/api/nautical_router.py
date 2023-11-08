from typing import Union
from fastapi import HTTPException, APIRouter, Depends, status
import subprocess
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import PlainTextResponse, JSONResponse
import os
import secrets
from authorize import authorize
from db import DB  # Replace with the actual name of your module containing the DB class

# All routes in this file start with /nautical
router = APIRouter(prefix="/api/v1/nautical", tags=["nautical"])

db = DB()
security = HTTPBasic()


@router.get("/db_dump", summary="Dump the entire database", response_class=JSONResponse)
def db_dump(credentials: HTTPBasicCredentials = Depends(security)):
    username = authorize(credentials)
    return db.dump_json()


@router.get(
    "/dashboard", summary="The most useful information", response_class=JSONResponse,
)
def dashboard(credentials: HTTPBasicCredentials = Depends(security)):
    """
    This returns a summary of the Nautical container. Useful for 3rd party applications.
    """
    username = authorize(credentials)
    return db.dump_json()


@router.post("/start_backup", summary="Start backup now", response_class=JSONResponse)
def start_backup(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Start a backup now. This respects all environment and docker labels.
    """
    username = authorize(credentials)
    try:
        # subprocess.run(['exec', 'nautical'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["nautical"], check=True)
        return {"message": f"Nautical Backup started successfully"}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=str(e.stderr.decode()))
