from typing import Any, Union, Optional
from fastapi import HTTPException, APIRouter, Depends, Path, status, BackgroundTasks
import subprocess
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import Annotated

from app.api.authorize import authorize
from app.api.utils import next_cron_occurrences
from app.db import DB

# All routes in this file start with /nautical
router = APIRouter(prefix="/api/v1/nautical", tags=["nautical"])

db = DB()


def kickoff_nautical():
    try:
        subprocess.run(["nautical"], check=True)
        return {"message": f"Nautical Backup completed successfully"}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=str(e.stderr.decode()))


@router.get("/dashboard", summary="The most useful information", response_class=JSONResponse)
def dashboard(username: Annotated[str, Depends(authorize)]) -> JSONResponse:
    """
    This returns a summary of the Nautical container. Useful for 3rd party applications.
    """

    next_crons = next_cron_occurrences(5)

    d = {
        "next_cron": next_crons,
        "next_run": next_crons.get("1", [None, None])[1] if next_crons else None,
        "last_cron": db.get("last_cron", "None"),
        "number_of_containers": db.get("number_of_containers", 0),
        "completed": db.get("containers_completed", 0),
        "skipped": db.get("containers_skipped", 0),
        "errors": db.get("errors", 0),
        "backup_running": db.get("containers_skipped", "false"),
    }
    return JSONResponse(content=jsonable_encoder(d))


@router.get(
    "/next_cron/{occurrences}",
    summary="Get the next CRON occurrences",
    response_class=JSONResponse,
)
def next_cron(
    username: Annotated[str, Depends(authorize)],
    occurrences: Annotated[int, Path(title="The ID of the item to get", ge=1, le=100)],
) -> JSONResponse:
    d = next_cron_occurrences(occurrences)
    res = JSONResponse(content=jsonable_encoder(d))
    return res


@router.post(
    "/start_backup",
    summary="Start backup now, will not respond until the backup has been completed.",
    response_class=JSONResponse,
)
def start_backup(username: Annotated[str, Depends(authorize)]):
    """
    Start a backup now and respond when completed. This respects all environment and docker labels.
    """
    return kickoff_nautical()


@router.post(
    "/kickoff_backup",
    summary="Start backup now, will immediatly respond even though the backup continues in the background",
    response_class=JSONResponse,
)
async def kickoff_backup(username: Annotated[str, Depends(authorize)], background_tasks: BackgroundTasks):
    """
    Start a backup now and respond immediately. This respects all environment and docker labels.
    """
    # Run the func 'kickoff_nautical' in the background, but return immediately
    background_tasks.add_task(kickoff_nautical)

    return {"message": f"Nautical Backup started successfully"}
