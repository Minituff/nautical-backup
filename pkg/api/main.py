from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import docker_router
import nautical_router
import os

# Read version from environment variable or default to '0.0.0' if not set
NAUTICAL_VERSION = os.getenv('NAUTICAL_VERSION', '0.0.0')

app = FastAPI(
    title="Nautical Backup",
    summary="A simple Docker volume backup tool 🚀",
    version=NAUTICAL_VERSION,
)

app.include_router(docker_router.router)
app.include_router(nautical_router.router)


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