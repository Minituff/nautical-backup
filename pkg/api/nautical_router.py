from typing import Union
from fastapi import HTTPException, APIRouter
import subprocess
from fastapi.responses import PlainTextResponse, JSONResponse
from db import DB  # Replace with the actual name of your module containing the DB class


# All routes in this file start with /nautical
router = APIRouter(
    prefix="/api/v1/nautical",
    tags=["nautical"]
)

db = DB()

@router.get("/db_dump", summary="Dump the entire database", response_class=JSONResponse)
def db_dump():
    return db.dump_json()

@router.get("/dashboard", summary="The most useful information", response_class=JSONResponse)
def dashboard():
    """
    This returns a summary of the Nautical container. Useful for 3rd party applications.
    """
    return db.dump_json()

@router.post("/start_backup", summary="Start backup now")
def start_backup():
    """
    Start a backup now. This respects all environment and docker labels.
    """
    try:
        # subprocess.run(['exec', 'nautical'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(['nautical'], check=True)
        return {"message": f"Nautical Backup started successfully"}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=str(e.stderr.decode()))