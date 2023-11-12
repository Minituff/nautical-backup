from typing import Union, Optional
from fastapi import HTTPException, APIRouter, Depends, status
import subprocess
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import PlainTextResponse, JSONResponse
import os
import secrets
from authorize import authorize
from utils import next_cron_occurrences
from typing import Annotated
from db import DB  # Replace with the actual name of your module containing the DB class


# All routes in this file start with /nautical
router = APIRouter(prefix="/api/v1/nautical", tags=["nautical"])

db = DB()


@router.get("/db_dump", summary="Dump the entire database", response_class=JSONResponse)
def db_dump(username: Annotated[str, Depends(authorize)]):
    return db.dump_json()


@router.get("/dashboard", summary="The most useful information", response_class=JSONResponse)
def dashboard(username: Annotated[str, Depends(authorize)]):
    """
    This returns a summary of the Nautical container. Useful for 3rd party applications.
    """
    return {
        "next_cron": next_cron_occurrences(5),
        "last_cron": db.get("last_cron", "None"),
        "number_of_containers": db.get("number_of_containers", 0),
        "completed": db.get("containers_completed", 0),
        "skipped": db.get("containers_skipped", 0),
        "errors": db.get("errors", 0),
        "backup_running": db.get("containers_skipped", "false"),
    }

@router.get("/next_cron/{occurrences}", summary="Get the next N amount of CRON occurrences", response_class=JSONResponse)
def next_cron(username: Annotated[str, Depends(authorize)], occurrences: Optional[int] = 5):
    return next_cron_occurrences(occurrences,)


@router.post("/start_backup", summary="Start backup now", response_class=JSONResponse)
def start_backup(username: Annotated[str, Depends(authorize)]):
    """
    Start a backup now. This respects all environment and docker labels.
    """
    try:
        # subprocess.run(['exec', 'nautical'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["nautical"], check=True)
        return {"message": f"Nautical Backup started successfully"}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=str(e.stderr.decode()))
