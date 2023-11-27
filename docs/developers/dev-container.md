
### 1. Verify Requirements

- [x] [Docker](https://code.visualstudio.com/remote/advancedcontainers/docker-options)
- [x] [Dev Containers VSCode extension](vscode:extension/ms-vscode-remote.remote-containers)

### 2. Open DevContainer
1. Clone to repo, then open it in VSCode.
1. Press ++ctrl+shift+p++
2. Then select `Dev Container: Open Folder in Container`
3. Wait for the container to build

### 3. Check the container

Once the container is running and you're connected, you should see `Dev Container: Nautical` in the bottom left of the Status bar.

## The `nb` command
The `nb` command gets installed as part of the [DevContainer](https://code.visualstudio.com/docs/devcontainers/create-dev-container) creation process.

```{.properties .no-copy}
nb --help

-- Nautical Backup Developer Commands: 
build          - Build Nautical container
run            - Run already built Nautical container
build-run      - Build and run Nautical container

build-test     - Build and run Nautical Testing container
test           - Run already built test Nautical container
build-test-run - Build and run Nautical Testing container

api            - Run the Python API locally
pytest         - Pytest locally and capture coverage
format         - Format all python code with black

docs           - Run the Nautical documentation locally
```