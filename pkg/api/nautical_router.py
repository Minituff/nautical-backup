from typing import Union
from fastapi import HTTPException, APIRouter
import subprocess
from fastapi.responses import PlainTextResponse

# All routes in this file start with /nautical
router = APIRouter(
    prefix="/api/v1/nautical",
    tags=["nautical"]
)
