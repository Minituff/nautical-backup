from typing import Union
from fastapi import HTTPException, APIRouter
import subprocess
from fastapi.responses import PlainTextResponse

# All routes in this file start with /docker
router = APIRouter(
    prefix="/api/v1/docker",
    tags=["docker"]
)

# New /docker_ps endpoint
@router.get("/ps", response_class=PlainTextResponse)
def docker_ps():
    # Run 'docker ps' command
    process = subprocess.Popen(['docker', 'ps'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    # Check if the command ran successfully
    if process.returncode == 0:
        # Return the result as a plain text
        return stdout.decode()
    else:
        # If an error occurred, return the error message
        return PlainTextResponse(stderr.decode(), status_code=500)

@router.get("/inspect/{container_name}", response_class=PlainTextResponse)
def docker_inspect(container_name: str):
    # Run 'docker inspect' with the provided container name
    process = subprocess.Popen(['docker', 'inspect', container_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    # Check if the command ran successfully
    if process.returncode == 0:
        # Return the result as a plain text
        return stdout.decode()
    else:
        # If an error occurred, raise an HTTPException with the error message
        raise HTTPException(status_code=500, detail=stderr.decode())
    
@router.post("/start/{container_name}")
def docker_start(container_name: str):
    try:
        subprocess.run(['docker', 'start', container_name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return {"message": f"Container {container_name} started successfully"}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=str(e.stderr.decode()))

@router.post("/stop/{container_name}")
def docker_stop(container_name: str):
    try:
        subprocess.run(['docker', 'stop', container_name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return {"message": f"Container {container_name} stopped successfully"}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=str(e.stderr.decode()))
