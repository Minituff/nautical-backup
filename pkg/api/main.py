from fastapi import FastAPI, HTTPException, APIRouter, Depends, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import docker_router
import nautical_router
import uvicorn
import os
import secrets
from authorize import authorize

# Read version from environment variable or default to '0.0.0' if not set
NAUTICAL_VERSION = os.getenv("NAUTICAL_VERSION", "0.0.0")

app = FastAPI(
    title="Nautical Backup",
    summary="A simple Docker volume backup tool 🚀",
    version=NAUTICAL_VERSION,
)

security = HTTPBasic()

# Import other endpoints
app.include_router(docker_router.router)
app.include_router(nautical_router.router)

@app.get("/api/access/auth")
def auth(credentials: HTTPBasicCredentials = Depends(security)):
    username = authorize(credentials)
    return {"Granted": True}

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>Nautical Backup</title>
        </head>
        <body>
            <h1>Looking for the API?</h1>
            <a href="/docs">Go here!</a>
        </body>
    </html>
    """


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8069, reload=True, log_level="debug")
