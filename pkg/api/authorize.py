from typing import Union
from fastapi import HTTPException, Depends, status, Security
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import PlainTextResponse, JSONResponse
import os
import secrets

ENV_USERNAME: str = os.getenv("HTTP_REST_API_USERNAME", "admin")
ENV_PASSWORD: str = os.getenv("HTTP_REST_API_PASSWORD", "password")

security = HTTPBasic()

def authorize(credentials: HTTPBasicCredentials = Depends(security)):    
    correct_username = secrets.compare_digest(credentials.username, ENV_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ENV_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username