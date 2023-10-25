# Contributing to the Documentation

This documentation is built using 2 major components:

1. [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) is a powerful documentation framework on top of [MkDocs](https://www.mkdocs.org), a static site generator for project documentation.

1. [MkDocs](https://www.mkdocs.org) is a fast, simple and downright gorgeous static site generator that's geared towards building project documentation. Documentation source files are written in `Markdown`, and configured with a single `YAML` configuration file.

## Running the Docs Locally
Spinning up the the docs locally ideal for development thanks to *hot reload*.

There are two easy ways to get MkDocs up and running locally:

1. [Docker](#docker) (easiest)
1. [Python and pip](#python-and-pip)

### Docker

If Docker is already installed on your machine, then running the docs locally is extrememly easy.

Verify Requirements
```bash
docker --version
# Docker version 20.10.22, build 3a2c30b

docker compose version
# Docker Compose version v2.15.1
```

The `docs/docker-compose.yml` file within the repo already has all the relavant information needed to get the docs up and running.
The official [Docker image](https://hub.docker.com/r/squidfunk/mkdocs-material/) already contains all the requierments

???+ abstract "Our `docker-compose.yml`"
   
    ```yaml
        # This file exists at docs/docker-compose.yml 
        version: "3"

        services:
        mkdocs:
            image: squidfunk/mkdocs-material:latest
            container_name: mkdocs
            hostname: mkdocs
            command: "" #(1)!
            volumes:
            - ../:/docs #(2)!
            ports:
            - 8000:8000
            restart: unless-stopped
    ```

    1. Serve the docs at http://127.0.0.1:8000
    2. This works only if we start the container from `docs` directory.

To start the container simply run the following command:
```bash
cd docs #(1)!
docker compose up
# [+] Running 1/0
# - Container mkdocs Created
# mkdocs  | INFO -  Serving on http://0.0.0.0:8000/
```

1. We need to run the `docker compose up` command from the `docs` directory.

MKDocs will now be avilable at: http://127.0.0.1:8000

### Python and pip

While the [Docker](#docker) method is the easiest to use, it's still quite simple to setup MKDocs using Python and pip.

Material for MkDocs is published as a [Python package](https://pypi.org/project/mkdocs-material/) and can be installed with
`pip`, ideally by using a [virtual environment](https://realpython.com/what-is-pip/#using-pip-in-a-python-virtual-environment).

1. Ensure you have **Python 3.8** or greater installed: 
   ```command
   python --version
   # Python 3.10.5
   ```
1. Clone repository to local machine and open in editor (VSCode recommended)
1. Set up virtual environment
   ```bash
   python -m venv .env
   ```
   You should now see a new folder titled `.env` in the project's root directory.

1. Activate virtual environment

    ```bash
    .env\Scripts\activate
    # (.env) ~ (1)
    ```

    1. Notice the `(.env)` in the terminal.
   
        This is how you know you have activated the virtual enviornment.


    !!! tip "About virtual environments"
        * Opening a new VSCode terminal will usually run `.env\Scripts\activate` automatically.

        ❗ **NOTE:** You will need to ensure the `env` is activated each time you open your IDE or terminal.

2. Install project plugins/libraries: 
   
    ```command
    pip install mkdocs-material
    ```
   
    !!! warning "Ensure you are in the virtual enviornment"

        If you are not in the `env` this will install the requirements to the main python directory, which is not ideal.

    This will automatically install compatible versions of all dependencies:

    [MkDocs](https://www.mkdocs.org/), [Markdown](https://python-markdown.github.io/), [Pygments](https://pygments.org/) and [Python Markdown Extensions](https://facelessuser.github.io/pymdown-extensions/).

3. Serve the docs:
   
    ```bash
    cd docs #(1)!
    mkdocs serve
    ```

    1. We must be in the docs direcory before serving
   

   MKDocs will now be avilable at: http://127.0.0.1:8000

<br>
<br>