from typing import Union
from fastapi import HTTPException, Depends, status, Security
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import PlainTextResponse, JSONResponse
from typing import Annotated
import os
import secrets

ENV_USERNAME: str = os.getenv("HTTP_REST_API_USERNAME", "admin")
ENV_PASSWORD: str = os.getenv("HTTP_REST_API_PASSWORD", "password")

security = HTTPBasic()

def authorize(credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = bytes(ENV_USERNAME, 'utf-8')
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = bytes(ENV_PASSWORD, 'utf-8')
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username