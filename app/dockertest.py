#!/usr/bin/python3

import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union
import sys
import subprocess
from pathlib import Path
from enum import Enum

import docker
from docker.models.containers import Container
from docker.errors import APIError


if __name__ == "__main__":
    docker_client = docker.from_env()
    print(docker_client.containers.list())
