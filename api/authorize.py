from typing import Union
from fastapi import HTTPException, Depends, status, Security
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import PlainTextResponse, JSONResponse
from typing import Annotated
import os
import secrets
from pydantic_settings import BaseSettings
from functools import lru_cache


from api.config import Settings

@lru_cache
def get_settings() -> Settings: 
    return Settings()


security = HTTPBasic()

def authorize(credentials: Annotated[HTTPBasicCredentials, Depends(security)], settings: Annotated[Settings, Depends(get_settings)]):
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = bytes(settings.HTTP_REST_API_USERNAME, "utf-8")
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = bytes(settings.HTTP_REST_API_PASSWORD, "utf-8")
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
