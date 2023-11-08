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

@router.get("/all", response_class=JSONResponse)
def all():
    return db.dump_json()