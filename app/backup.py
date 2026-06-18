#!/usr/bin/env python3

import copy
import os
import shutil
import subprocess
import sys
import time
import codecs
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import docker
from docker.errors import APIError, ImageNotFound
from docker.models.containers import Container
from requests.exceptions import ReadTimeout

from app.api.config import Settings
from app.db import DB
from app.logger import Logger, LogType
from app.nautical_env import NauticalEnv


class BeforeOrAfter(Enum):
    BEFORE = 1
    AFTER = 2


class BeforeAfterorDuring(Enum):
    BEFORE = 1
    AFTER = 2
    DURING = 3


class NauticalBackup:
    def __init__(self, docker_client: docker.DockerClient):
        self.db = DB()
        self.env = NauticalEnv()
        self.logger = Logger()
        self.settings = Settings()
        self.docker = docker_client
        self.default_group_pfx_sfx = "&"  # The prefix and suffix used to define this group

        self.containers_completed = set()
        self.containers_skipped = set()
        self.containers_failed = set()
        self.container_skip_reasons: Dict[str, str] = {}
        self.container_failure_reasons: Dict[str, str] = {}
        self.error_messages: List[str] = []
        self.prefix = self.env.LABEL_PREFIX

        # Grab the backup starting time
        self.start_time = datetime.now()

        if self.env.REPORT_FILE == True and self.env.REPORT_FILE_ON_BACKUP_ONLY == False:
            self.logger._create_new_report_file()

        self.verify_nautical_mounted_source_location(self.env.SOURCE_LOCATION)
        self.verify_nautical_mounted_destination_location(self.env.DEST_LOCATION, create_if_not_exists=False)

    def log_this(self, log_message, log_priority="INFO", log_type=LogType.DEFAULT) -> None:
        """Wrapper for log this"""
        return self.logger.log_this(log_message, log_priority, log_type)

    def _format_set_for_exec(self, input_set: set) -> str:
        """Return stable comma-separated values for script-friendly env vars."""
        return ",".join(sorted(str(i) for i in input_set))

    def _format_reasons_for_exec(self, reasons: Dict[str, str]) -> str:
        """Return stable semicolon-separated name=reason pairs for script-friendly env vars."""
        return ";".join(f"{name}={reason}" for name, reason in sorted(reasons.items()))

    def _format_error_messages_for_exec(self) -> str:
        cleaned_messages = []
        for message in self.error_messages:
            cleaned_messages.append(str(message).replace("\n", " ").replace(";", ",").strip())
        return ";".join(cleaned_messages)

    def _record_error(self, message: str) -> None:
        if message not in self.error_messages:
            self.error_messages.append(message)

    def _record_container_skipped(self, c: Container, reason: str, message: str, log=True, level: str = "INFO") -> None:
        self.containers_skipped.add(c.name)
        self.container_skip_reasons.setdefault(c.name if c.name else str(c.id), reason)
        if log:
            self.log_this(message, level)

    def _record_container_failed(self, c: Container, reason: str, message: str, log=True) -> None:
        self.containers_failed.add(c.name)
        self.container_failure_reasons.setdefault(c.name if c.name else str(c.id), reason)
        self._record_error(message)
        if log:
            self.log_this(message, "ERROR")

    def _backup_status(self) -> str:
        if self.containers_failed or self.error_messages:
            return "error"
        if self.containers_skipped:
            return "warning"
        return "success"

    def _reset_outcomes(self) -> None:
        self.containers_completed.clear()
        self.containers_skipped.clear()
        self.containers_failed.clear()
        self.container_skip_reasons.clear()
        self.container_failure_reasons.clear()
        self.error_messages.clear()

    def get_label(self, container: Container, target: str, default=None):
        """Apply the label prefix and return the label value
        By default the label will look like: `nautical-backup.enable`
        """
        return container.labels.get(f"{self.prefix}.{target}", default)

    def verify_nautical_mounted_source_location(self, src_dir: str):
        self.log_this(f"Verifying source directory '{src_dir}'...", "DEBUG", LogType.INIT)
        if not os.path.isdir(src_dir):
            self.log_this(f"Source directory '{src_dir}' does not exist.", "ERROR", LogType.INIT)
            raise FileNotFoundError(f"Source directory '{src_dir}' does not exist.")
        elif not os.access(src_dir, os.R_OK):
            self.log_this(f"No read access to source directory '{src_dir}'.", "ERROR", LogType.INIT)
            raise PermissionError(f"No read access to source directory '{src_dir}'")

        self.log_this(f"Source directory '{src_dir}' READ access verified", "TRACE", LogType.INIT)

    def verify_nautical_mounted_destination_location(self, dest_dir: Union[str, Path], create_if_not_exists=True):
        self.log_this(f"Verifying Nautical destination directory '{dest_dir}'...", "DEBUG", LogType.INIT)

        if not os.path.exists(dest_dir) and create_if_not_exists:
            os.makedirs(dest_dir, exist_ok=True)

        if not os.path.isdir(dest_dir):
            self.log_this(
                f"Destination directory '{dest_dir}' does not exist. Please mount it to /app/destination",
                "ERROR",
                LogType.INIT,
            )
            raise FileNotFoundError(f"Destination directory '{dest_dir}' does not exist.")
        elif not os.access(dest_dir, os.R_OK):
            self.log_this(f"No read access to destination directory '{dest_dir}'.", "ERROR", LogType.INIT)
            raise PermissionError(f"No read access to destination directory '{dest_dir}'")
        elif not os.access(dest_dir, os.W_OK):
            self.log_this(f"No write access to destination directory '{dest_dir}'.", "ERROR", LogType.INIT)
            raise PermissionError(f"No write access to destination directory '{dest_dir}'")

        self.log_this(f"Destination directory '{dest_dir}' READ/WRITE access verified", "TRACE", LogType.INIT)

    def verify_destination_location(self, dest_dir: Union[str, Path], create_if_not_exists=True) -> bool:
        """Verify the destination location (for containers) exists and is writable"""
        self.log_this(f"Verifying destination directory '{dest_dir}'...", "DEBUG", LogType.INIT)

        if not os.path.exists(dest_dir) and create_if_not_exists:
            os.makedirs(dest_dir, exist_ok=True)

        if not os.path.isdir(dest_dir):
            self.log_this(
                f"Destination directory '{dest_dir}' does not exist. Please mount it to /app/destination", "ERROR"
            )
            return False
        elif not os.access(dest_dir, os.R_OK):
            self.log_this(f"No read access to destination directory '{dest_dir}'.", "ERROR")
            return False
        elif not os.access(dest_dir, os.W_OK):
            self.log_this(f"No write access to destination directory '{dest_dir}'.", "ERROR")
            raise PermissionError(f"No write access to destination directory '{dest_dir}'")

        self.log_this(f"Destination directory '{dest_dir}' READ/WRITE access verified", "TRACE")
        return True

    def _should_skip_container(self, c: Container) -> bool:
        """Use logic to determine if a container should be skipped by nautical completely"""

        SELF_CONTAINER_ID = self.env.SELF_CONTAINER_ID  # Used to skip self

        try:
            # Attempt to pull info from container. Skip if not found
            info = str(c.name) + " " + str(c.id) + " " + str(c.image) + " " + str(c.labels)
        except ImageNotFound as e:
            self._record_container_skipped(
                c, "image_not_found", "Skipping container because its info was not found.", level="WARN"
            )
            return True

        if "minituff/nautical-backup" in str(c.image):
            self._record_container_skipped(
                c,
                "nautical_backup_image",
                f"Skipping {c.name} {c.id} because its image matches 'minituff/nautical-backup'.",
            )
            return True
        if c.labels.get("org.opencontainers.image.title") == "nautical-backup":
            self._record_container_skipped(
                c,
                "nautical_backup_image",
                f"Skipping {c.name} {c.id} because its image matches 'nautical-backup'.",
            )
            return True
        if c.id == SELF_CONTAINER_ID:
            self._record_container_skipped(
                c, "self_container", f"Skipping {c.name} {c.id} because its ID is the same as Nautical"
            )
            return True
        if c.name == SELF_CONTAINER_ID:
            self._record_container_skipped(
                c, "self_container", f"Skipping {c.name} because its ID is the same as Nautical"
            )
            return True

        # Read the environment variables
        SKIP_CONTAINERS = self.env.SKIP_CONTAINERS

        # Convert the strings into lists
        skip_containers_set = set(SKIP_CONTAINERS.split(","))

        nautical_backup_enable_str = str(self.get_label(c, "enable", ""))
        if nautical_backup_enable_str.lower() == "false":
            nautical_backup_enable = False
        elif nautical_backup_enable_str.lower() == "true":
            nautical_backup_enable = True
        else:
            nautical_backup_enable = None

        if nautical_backup_enable == False:
            self._record_container_skipped(c, "enable_label_false", f"Skipping {c.name} based on label")
            return True

        if self.env.REQUIRE_LABEL == True and nautical_backup_enable is not True:
            self._record_container_skipped(
                c,
                "require_label_missing",
                f"Skipping {c.name} as '{self.prefix}.enable=true' was not found and REQUIRE_LABEL is true.",
            )
            return True

        if c.name in skip_containers_set:
            self._record_container_skipped(c, "skip_containers_name", f"Skipping {c.name} based on name")
            return True

        if c.id in skip_containers_set:
            self._record_container_skipped(c, "skip_containers_id", f"Skipping {c.name} based on ID {c.id}")
            return True

        # No reason to skip
        return False

    def group_containers(self) -> Dict[str, List[Container]]:
        containers: List[Container] = self.docker.containers.list()  # type: ignore
        starting_container_amt = len(containers)
        self.log_this(f"Processing {starting_container_amt} containers...", "INFO")

        self.db.put("number_of_containers", starting_container_amt)

        output = ""
        for container in containers:
            output += str(container.name) + ", "
        output = output[:-2]
        self.log_this(f"Containers: {output}", "DEBUG")

        containers_by_group_in_process: Dict[str, List[Tuple[int, Container]]] = {}

        for c in containers:
            if self._should_skip_container(c) == True:
                continue  # Skip this container

            # Create a default group, so ungrouped items are not grouped together
            default_group = f"{self.default_group_pfx_sfx}{str(c.id)[0:12]}{self.default_group_pfx_sfx}"
            group = str(self.get_label(c, "group", default_group))
            if not group or group == "":
                group = default_group

            # Split the group string into a list of groups by comma
            groups = group.split(",")
            for g in groups:
                # Get priority. Default=100
                priority = int(self.get_label(c, f"group.{g}.priority", 100))

                if g not in containers_by_group_in_process:
                    containers_by_group_in_process[g] = [(priority, c)]
                else:
                    containers_by_group_in_process[g].append((priority, c))

        # Create final return dictionary
        containers_by_group: Dict[str, List[Container]] = {}

        # Sort the groups by priority (highest first)
        for group, pri_and_cont in containers_by_group_in_process.items():
            new_pri_and_cont = sorted(pri_and_cont, key=lambda pri: pri[0])
            new_pri_and_cont.reverse()

            for pri, cont in new_pri_and_cont:
                if group not in containers_by_group:
                    containers_by_group[group] = [cont]
                else:
                    containers_by_group[group].append(cont)

        return containers_by_group

    def _set_exec_environment_variables(self, vars: Dict[str, str]):
        """Set the environment variables for the exec command"""
        for k, v in vars.items():  # Loop through all the variables in the class
            self.log_this(f"Setting environment variable {k} to {v}", "TRACE")
            os.environ[k] = v  # Set the environment variable

    def _run_exec(
        self,
        c: Optional[Container],
        when: BeforeAfterorDuring,
        attached_to_container=False,
    ) -> Optional[subprocess.CompletedProcess[bytes]]:
        """Runs a exec command from the Nautical Container itself."""
        command = ""  # Curl command

        if attached_to_container == True and c:
            if when == BeforeAfterorDuring.BEFORE:
                curl_command = str(self.get_label(c, "curl.before", ""))
                command = str(self.get_label(c, "exec.before", curl_command))

                if curl_command and curl_command != "":
                    self.log_this(
                        f"Deprecated: '{self.prefix}.curl.before' has been moved to '{self.prefix}.exec.before'",
                        "WARN",
                    )
                if command and command != "":
                    self.log_this("Running PRE-backup exec command for $name", "DEBUG")
            elif when == BeforeAfterorDuring.DURING:
                curl_command = str(self.get_label(c, "curl.during", ""))
                command = str(self.get_label(c, "exec.during", curl_command))

                if curl_command and curl_command != "":
                    self.log_this(
                        f"Deprecated: '{self.prefix}.curl.during' has been moved to '{self.prefix}.exec.during'",
                        "WARN",
                    )
                if command and command != "":
                    self.log_this("Running DURING-backup exec command for $name", "DEBUG")
            elif when == BeforeAfterorDuring.AFTER:
                curl_command = str(self.get_label(c, "curl.after", ""))
                command = str(self.get_label(c, "exec.after", curl_command))
                if curl_command and curl_command != "":
                    self.log_this(
                        f"Deprecated: '{self.prefix}.curl.after' has been moved to '{self.prefix}.exec.after'",
                        "WARN",
                    )
                if command and command != "":
                    self.log_this("Running AFTER-backup exec command for $name", "DEBUG")
            else:
                return None
        else:
            nautical_env = NauticalEnv()

            if when == BeforeAfterorDuring.BEFORE:
                curl_command = str(nautical_env._PRE_BACKUP_CURL)
                if curl_command and curl_command != "":
                    self.log_this("Deprecated: PRE_BACKUP_CURL has been moved to PRE_BACKUP_EXEC", "WARN")

                command = str(nautical_env.PRE_BACKUP_EXEC)
                if command and command != "":
                    self.log_this("Running PRE_BACKUP_EXEC", "DEBUG")
            elif when == BeforeAfterorDuring.AFTER:
                curl_command = str(nautical_env._POST_BACKUP_CURL)
                if curl_command and curl_command != "":
                    self.log_this("Deprecated: POST_BACKUP_CURL has been moved to POST_BACKUP_EXEC", "WARN")

                command = str(nautical_env.POST_BACKUP_EXEC)
                if command and command != "":
                    self.log_this("Running POST_BACKUP_EXEC", "DEBUG")
            else:
                return None

        # Example command "curl -o /app/destination/google google.com"
        if not str(command) or str(command) == "" or str(command) == "None":
            return None

        vars: Dict[str, str] = {
            "NB_EXEC_COMMAND": str(command),
            "NB_EXEC_ATTACHED_TO_CONTAINER": str(attached_to_container),
            "NB_EXEC_CONTAINER_NAME": str(c.name) if c else "None",
            "NB_EXEC_CONTAINER_ID": str(c.id) if c else "None",
            "NB_EXEC_BEFORE_DURING_OR_AFTER": str(when.name),
        }

        # Add environment variables to the command (after all containers are done)
        if when == BeforeAfterorDuring.AFTER and attached_to_container == False:
            vars["NB_EXEC_TOTAL_ERRORS"] = str(self.db.get("errors", ""))
            vars["NB_EXEC_TOTAL_CONTAINERS_COMPLETED"] = str(self.db.get("containers_completed", ""))
            vars["NB_EXEC_TOTAL_CONTAINERS_SKIPPED"] = str(self.db.get("containers_skipped", ""))
            vars["NB_EXEC_TOTAL_NUMBER_OF_CONTAINERS"] = str(self.db.get("number_of_containers", ""))
            vars["NB_EXEC_BACKUP_STATUS"] = self._backup_status()
            vars["NB_EXEC_BACKUP_STARTED_AT"] = self.start_time.isoformat()
            vars["NB_EXEC_BACKUP_FINISHED_AT"] = getattr(self, "end_time", datetime.now()).isoformat()
            vars["NB_EXEC_BACKUP_DURATION_SECONDS"] = str(self.db.get("last_backup_seconds_taken", ""))
            vars["NB_EXEC_CONTAINERS_COMPLETED"] = self._format_set_for_exec(self.containers_completed)
            vars["NB_EXEC_CONTAINERS_SKIPPED"] = self._format_set_for_exec(self.containers_skipped)
            vars["NB_EXEC_CONTAINERS_FAILED"] = self._format_set_for_exec(self.containers_failed)
            vars["NB_EXEC_CONTAINER_SKIP_REASONS"] = self._format_reasons_for_exec(self.container_skip_reasons)
            vars["NB_EXEC_CONTAINER_FAILURE_REASONS"] = self._format_reasons_for_exec(self.container_failure_reasons)
            vars["NB_EXEC_ERROR_MESSAGES"] = self._format_error_messages_for_exec()

        self._set_exec_environment_variables(vars)

        self.log_this(f"Running EXEC command: {command}")
        out = subprocess.run(command, shell=True, executable="/bin/bash", capture_output=True)

        if out.stderr and isinstance(out.stderr, bytes) or isinstance(out.stderr, str):
            self.log_this(f"Exec command error: {codecs.decode(out.stderr, 'utf-8').strip()}", "WARN")

        if out.stdout and isinstance(out.stdout, bytes) or isinstance(out.stdout, str):
            self.log_this(f"Exec command output: {codecs.decode(out.stdout, 'utf-8').strip()}", "DEBUG")

        return out

    def _run_lifecyle_hook(self, c: Container, when: BeforeOrAfter):
        """Runs a commend inside the child container"""
        if when == BeforeOrAfter.BEFORE:
            command = str(self.get_label(c, "lifecycle.before", ""))
            timeout = str(self.get_label(c, "lifecycle.before.timeout", "60"))
            if command and command != "":
                self.log_this("Running DURING-backup lifecycle hook for $name", "DEBUG")
        elif when == BeforeOrAfter.AFTER:
            timeout = str(self.get_label(c, "lifecycle.after.timeout", "60"))
            command = str(self.get_label(c, "lifecycle.after", ""))
            if command and command != "":
                self.log_this("Running AFTER-backup lifecycle hook for $name", "DEBUG")
        else:
            return
        if not command or command == "":
            return None

        command = f"timeout {timeout} " + command

        self.log_this(f"RUNNING '{command}'", "DEBUG")
        c.exec_run(command)

    def _stop_container(self, c: Container, attempt=1) -> bool:
        c.reload()  # Refresh the status for this container

        SKIP_STOPPING = self.env.SKIP_STOPPING
        skip_stopping_set = set(SKIP_STOPPING.split(","))
        if c.name in skip_stopping_set or c.id in skip_stopping_set:
            self.log_this(f"Container {c.name} is in SKIP_STOPPING list. Will not stop container.", "DEBUG")
            return True

        stop_before_backup = str(self.get_label(c, "stop-before-backup", "true"))
        if stop_before_backup.lower() == "false":
            self.log_this(f"Skipping stopping of {c.name} because of label", "DEBUG")
            return True
        if c.status != "running":
            self.log_this(f"Container {c.name} was not running. No need to stop.", "DEBUG")
            return True

        stop_timeout = str(self.get_label(c, "stop-timeout", str(self.env.STOP_TIMEOUT)))
        stop_timeout = int(stop_timeout)

        self.log_this(f"Stopping {c.name}...", "INFO")
        try:
            c.stop(timeout=stop_timeout)  # * Actually stop the container
        except ReadTimeout:
            self.log_this(f"Timed out waiting for {c.name} to stop. Checking container status...", "WARN")
            # Fall through to c.reload() — container may have stopped despite the timeout
        except APIError as e:
            self.log_this(f"Error stopping container {c.name}. Skipping backup for this container.", "ERROR")
            return False

        c.reload()  # Refresh the status for this container
        if c.status == "exited":
            return True
        elif attempt <= 3:
            self.log_this(f"Container {c.name} was not in exited state. Trying again (Attempt {attempt}/3)", "ERROR")
            self._stop_container(c, attempt=attempt + 1)
        return False

    def _start_container(self, c: Container, attempt=1, max_attempts: Optional[int] = None) -> bool:
        if max_attempts is None:
            start_timeout = int(self.get_label(c, "start-timeout", str(self.env.START_TIMEOUT)))
            max_attempts = max(1, (start_timeout // 2) + 1)
            self.log_this(f"Container {c.name}: start-timeout={start_timeout}s (max_attempts={max_attempts})", "DEBUG")

        c.reload()  # Refresh the status for this container
        status = c.status  # Read once to avoid consuming multiple mock cycles

        if status == "running":
            if attempt == 1:
                self.log_this(f"Container {c.name} was not stopped. No need to start.", "DEBUG")
            else:
                self.log_this(f"Container {c.name} is now running.", "INFO")
            return True

        if status != "exited":
            # Transitional state: Docker statuses are created/restarting/running/paused/exited/dead
            if attempt <= max_attempts:
                self.log_this(
                    f"Container {c.name} is in '{status}' state, waiting for it to stabilize (Attempt {attempt}/{max_attempts})",
                    "WARN",
                )
                time.sleep(2)
                return self._start_container(c, attempt=attempt + 1, max_attempts=max_attempts)
            return False

        try:
            self.log_this(f"Starting {c.name}...")
            c.start()  # * Actually start the container
        except ReadTimeout:
            self.log_this(f"Timed out waiting for {c.name} to start. Checking container status...", "WARN")
            # Fall through to c.reload() — container may have started despite the timeout
        except APIError as e:
            self.log_this(f"Error starting container {c.name}.", "ERROR")
            return False

        c.reload()  # Refresh the status for this container
        status = c.status  # Read once to avoid consuming multiple mock cycles

        if status == "running":
            if attempt > 1:
                self.log_this(f"Container {c.name} is now running.", "INFO")
            return True
        elif attempt <= max_attempts:
            self.log_this(
                f"Container {c.name} was not in running state. Trying again (Attempt {attempt}/{max_attempts})", "WARN"
            )
            return self._start_container(c, attempt=attempt + 1, max_attempts=max_attempts)
        return False

    def _get_src_dir(self, c: Container, log=False) -> Tuple[Path, str]:
        """Get the source directory for the container
        Returns a tuple of the source directory and the source directory name
        """
        base_src_dir = Path(self.env.SOURCE_LOCATION)
        src_dir_no_path = str(c.name)
        src_dir: Path = base_src_dir / src_dir_no_path

        if str(c.name) in self.env.OVERRIDE_SOURCE_DIR:
            print("FOUND OVERRIDE for", c.name, self.env.OVERRIDE_SOURCE_DIR[str(c.name)])
            new_src_dir = self.env.OVERRIDE_SOURCE_DIR[str(c.name)]
            src_dir = base_src_dir / new_src_dir
            src_dir_no_path = new_src_dir
            if log == True:
                self.log_this(f"Overriding source directory for {c.name} to '{new_src_dir}'")

        if str(c.id) in self.env.OVERRIDE_SOURCE_DIR:
            new_src_dir = self.env.OVERRIDE_SOURCE_DIR[str(c.id)]
            src_dir = base_src_dir / new_src_dir
            src_dir_no_path = new_src_dir
            if log == True:
                self.log_this(f"Overriding source directory for {c.id} to '{new_src_dir}'")

        label_src = str(self.get_label(c, "override-source-dir", ""))
        if label_src and label_src != "":
            if log == True:
                self.log_this(f"Overriding source directory for {c.name} to '{label_src}' from label")
            src_dir = base_src_dir / label_src
            src_dir_no_path = label_src

        return src_dir, src_dir_no_path

    def _get_label_src_dirs(self, c: Container) -> List[Tuple[Path, str]]:
        """Return list of (src_dir, src_dir_no_path) honoring comma-separated override-source-dir labels.
        Falls back to _get_src_dir (which includes env var overrides) when the label is absent.
        """
        base_src_dir = Path(self.env.SOURCE_LOCATION)
        label_src = str(self.get_label(c, "override-source-dir", ""))
        if not label_src:
            return [self._get_src_dir(c)]
        folders = [f.strip() for f in label_src.split(",") if f.strip()]
        return [(base_src_dir / f, f) for f in folders]

    def _get_dest_dir(self, c: Container, src_dir_name: str) -> Tuple[Path, str]:
        base_dest_dir = Path(self.env.DEST_LOCATION)
        dest_dir_full: Path = base_dest_dir / str(c.name)
        dest_dir_name = str(c.name)

        keep_src_dir_name_label = str(self.get_label(c, "keep_src_dir_name", "")).lower()

        # This allows the user to set the KEEP_SRC_DIR_NAME environment variable to override the label's default if set
        # But the label will still override the environment variable if set to false/true
        if str(self.env.KEEP_SRC_DIR_NAME).lower() == "" and keep_src_dir_name_label == "":
            keep_src_dir_name_label = "true"

        if str(self.env.KEEP_SRC_DIR_NAME).lower() == "true" and keep_src_dir_name_label != "false":
            dest_dir_full: Path = base_dest_dir / src_dir_name
            dest_dir_name = src_dir_name

        if keep_src_dir_name_label == "true":
            dest_dir_full: Path = base_dest_dir / src_dir_name
            dest_dir_name = src_dir_name

        if str(c.name) in self.env.OVERRIDE_DEST_DIR:
            new_dest_dir = self.env.OVERRIDE_DEST_DIR[str(c.name)]
            dest_dir_full = base_dest_dir / new_dest_dir
            dest_dir_name = new_dest_dir
            self.log_this(f"Overriding destination directory for {c.name} to '{new_dest_dir}'")

        if str(c.id) in self.env.OVERRIDE_DEST_DIR:
            new_dest_dir = self.env.OVERRIDE_DEST_DIR[str(c.id)]
            dest_dir_full = base_dest_dir / new_dest_dir
            dest_dir_name = new_dest_dir
            self.log_this(f"Overriding destination directory for {c.id} to '{new_dest_dir}'")

        label_dest = str(self.get_label(c, "override-destination-dir", ""))
        if label_dest and label_dest != "":
            self.log_this(f"Overriding destination directory for {c.name} to '{label_dest}' from label")
            dest_dir_full = base_dest_dir / label_dest
            dest_dir_name = label_dest

        dest_dir_no_path = dest_dir_name  # Assigment to userstand they are the same thing
        if str(self.env.USE_DEST_DATE_FOLDER).lower() == "true":
            # Final name of the actual folder

            # Use Nautical start time as the date for formatting
            time_format = str(self.start_time.strftime(self.env.DEST_DATE_FORMAT))
            if self.env.USE_CONTAINER_BACKUP_DATE:
                # Use current time for formatting
                self.log_this(f"Using current time for date formatting since USE_CONTAINER_BACKUP_DATE=true", "Trace")
                time_format = str(time.strftime(self.env.DEST_DATE_FORMAT))

            if str(self.env.DEST_DATE_PATH_FORMAT) == "container/date":
                dest_dir_no_path = f"{dest_dir_name}/{time_format}"
                dest_dir_full: Path = base_dest_dir / dest_dir_name / time_format
            elif str(self.env.DEST_DATE_PATH_FORMAT) == "date/container":
                dest_dir_full: Path = base_dest_dir / time_format / dest_dir_name
                dest_dir_no_path = f"{time_format}/{dest_dir_name}"

            if not os.path.exists(dest_dir_full):
                os.makedirs(dest_dir_full, exist_ok=True)

        return dest_dir_full, dest_dir_no_path

    def _format_dated_folder(self, base_dest_dir: Path, folder: str) -> Path:
        """Format the destination folder with the date"""

        # Use Nautical start time as the date for formatting
        time_format = str(self.start_time.strftime(self.env.DEST_DATE_FORMAT))
        if self.env.USE_CONTAINER_BACKUP_DATE:
            # Use current time for formatting
            self.log_this(f"Using current time for date formatting since USE_CONTAINER_BACKUP_DATE=true", "Trace")
            time_format = str(time.strftime(self.env.DEST_DATE_FORMAT))

        if str(self.env.DEST_DATE_PATH_FORMAT) == "container/date":
            dest_dir: Path = base_dest_dir / folder / time_format
        elif str(self.env.DEST_DATE_PATH_FORMAT) == "date/container":
            dest_dir: Path = base_dest_dir / time_format / folder

        return dest_dir

    def _backup_additional_folders_standalone(self, when: BeforeOrAfter, base_dest_dir: Path):
        """Backup folders that are not associated with a container."""
        additional_folders = str(self.env.ADDITIONAL_FOLDERS)
        additional_folders_when = str(self.env.ADDITIONAL_FOLDERS_WHEN)

        # Ensure backups is only run when it should be
        if additional_folders_when == "before" and when != BeforeOrAfter.BEFORE:
            return
        if additional_folders_when == "after" and when != BeforeOrAfter.AFTER:
            return

        base_src_dir = Path(self.env.SOURCE_LOCATION)

        self.verify_destination_location(base_dest_dir)
        if not os.path.exists(base_dest_dir):
            self.log_this(
                f"Destination directory '{base_dest_dir}' does not exist during {BeforeOrAfter.BEFORE.name}", "ERROR"
            )
            return

        rsync_args = self._get_rsync_args(None, log=False)

        for folder in additional_folders.split(","):
            if folder == "":
                continue

            src_dir = base_src_dir / folder
            dest_dir = base_dest_dir / folder

            if str(self.env.ADDITIONAL_FOLDERS_USE_DEST_DATE_FOLDER).lower() == "true":
                dest_dir = self._format_dated_folder(base_dest_dir, folder)

                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir, exist_ok=True)

            self.log_this(f"Backing up standalone additional folder '{folder}'")
            self._run_rsync(None, rsync_args, src_dir, dest_dir)

    def _backup_additional_folders(self, c: Container, base_dest_dir: Path):
        additional_folders = str(self.get_label(c, "additional-folders", ""))
        base_src_dir = Path(self.env.SOURCE_LOCATION)

        rsync_args = self._get_rsync_args(c, log=False)

        for folder in additional_folders.split(","):
            if not folder or folder.strip() == "":
                continue

            src_dir = base_src_dir / folder
            dest_dir = base_dest_dir / folder

            if str(self.env.USE_DEST_DATE_FOLDER).lower() == "true":
                dest_dir = self._format_dated_folder(base_dest_dir, folder)

                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir, exist_ok=True)

            self.verify_destination_location(dest_dir)
            self.log_this(f"Backing up additional folder '{folder}' for container {c.name}")
            self._run_rsync(c, rsync_args, src_dir, dest_dir)

    def _backup_container_folders(self, c: Container, dest_path: Optional[Path] = None):
        is_secondary = dest_path is not None
        if not dest_path:
            dest_path = Path(self.env.DEST_LOCATION)

        src_dir_required = str(self.get_label(c, "source-dir-required", "true")).lower()
        if src_dir_required == "true":
            self.verify_destination_location(dest_path)

        rsync_args = self._get_rsync_args(c)

        for src_dir, src_dir_no_path in self._get_label_src_dirs(c):
            dest_dir, dest_dir_no_path = self._get_dest_dir(c, src_dir_no_path)
            if is_secondary:
                dest_dir = dest_path / dest_dir_no_path

            if src_dir_required == "true" and not dest_dir.exists():
                self.log_this(f"Destination directory '{dest_dir}' does not exist", "ERROR")

            if src_dir.exists():
                os.makedirs(dest_dir, exist_ok=True)
                self.log_this(f"Backing up {c.name}...", "INFO")

                rsync_ok = self._run_rsync(c, rsync_args, src_dir, dest_dir)
                if not rsync_ok:
                    self._record_container_skipped(
                        c, "rsync_failed", f"Skipping completion of {c.name} because rsync failed", log=False
                    )
            elif src_dir_required == "false":
                # Do nothing. This container is still started and stopped, but there is nothing to backup
                # Likely this container is part of a group and the source directory is not required
                pass
            else:
                self._record_container_skipped(
                    c, "source_directory_missing", f"Source directory {src_dir} does not exist. Skipping", level="WARN"
                )

        additional_folders_when = str(self.get_label(c, "additional-folders.when", "during")).lower()
        if not additional_folders_when or additional_folders_when == "during":
            self._backup_additional_folders(c, dest_path)

    def _run_rsync(self, c: Optional[Container], rsync_args: str, src_dir: Path, dest_dir: Path) -> bool:
        src_folder = f"{src_dir.absolute()}/"
        dest_folder = f"{dest_dir.absolute()}/"

        command = f"{rsync_args} {src_folder} {dest_folder}"

        self.log_this(f"RUNNING: 'rsync {command}'", "DEBUG")

        # args = command.split()  # Split the command into a list of arguments
        out = subprocess.run(f"/usr/bin/rsync {command}", shell=True, capture_output=False)
        # out = subprocess.run(args, shell=True, executable="/usr/bin/rsync", capture_output=False)

        if out.returncode != 0:
            name = c.name if c else "unknown"
            message = f"rsync exited with code {out.returncode} for {name}"
            if out.returncode == 23:
                # Exit code 23 = partial transfer; commonly caused by symlinks on filesystems
                # that don't support them (e.g. SMB/FAT). Regular files are still backed up.
                hint = " (symlinks may have been skipped — use RSYNC_CUSTOM_ARGS=--no-links to suppress)"
                if c:
                    self._record_container_failed(c, "rsync_failed", message + hint)
                else:
                    self._record_error(message + hint)
                    self.log_this(message + hint, "ERROR")
                return False
            if c:
                self._record_container_failed(c, "rsync_failed", message)
            else:
                self._record_error(message)
                self.log_this(message, "ERROR")
            return False
        return True

    def _get_rsync_args(self, c: Optional[Container], log=False) -> str:
        default_rsync_args = self.env.DEFAULT_RNC_ARGS
        custom_rsync_args = ""
        used_default_args = True

        if str(self.env.USE_DEFAULT_RSYNC_ARGS).lower() == "false":
            if log == True:
                self.log_this(f"Disabling default rsync arguments ({self.env.DEFAULT_RNC_ARGS})", "DEBUG")
            default_rsync_args = ""

        if c:
            use_default_args = str(self.get_label(c, "use-default-rsync-args", "")).lower()
            if use_default_args == "false":
                if log == True:
                    self.log_this(f"Disabling default rsync arguments ({self.env.DEFAULT_RNC_ARGS})", "DEBUG")
                default_rsync_args = ""

        if str(self.env.RSYNC_CUSTOM_ARGS) != "":
            custom_rsync_args = str(self.env.RSYNC_CUSTOM_ARGS)
            if log == True:
                self.log_this(f"Adding custom rsync arguments ({custom_rsync_args})", "DEBUG")
            used_default_args = False

        if c:
            custom_rsync_args_label = str(self.get_label(c, "rsync-custom-args", ""))
            if custom_rsync_args_label != "":
                if log == True:
                    self.log_this(f"Setting custom rsync args from label ({custom_rsync_args_label})", "DEBUG")
                custom_rsync_args = custom_rsync_args_label
                used_default_args = False

        if log == True:
            if used_default_args == True:
                self.log_this(f"Using default rsync arguments ({self.env.DEFAULT_RNC_ARGS})", "DEBUG")
            else:
                self.log_this(f"Using custom rsync arguments ({custom_rsync_args})", "DEBUG")

        return f"{default_rsync_args} {custom_rsync_args}"

    def _apply_retention_policy(self, base_dest_dir: Path) -> None:
        """Delete old date-stamped backup folders, keeping the N most recent backups.

        Only runs when NUMBER_OF_BACKUPS_TO_KEEP > 0 and USE_DEST_DATE_FOLDER is true.
        Folders whose names cannot be parsed with DEST_DATE_FORMAT are left untouched.
        When RETENTION_DRY_RUN is true, candidates are logged but nothing is deleted.

        Path formats are pruned according to their folder shape:
          - container/date: destination/<container>/<date>/  — date folders pruned per container dir
          - date/container: destination/<date>/<container>/  — date folders pruned as atomic backup sets
        """
        backups_to_keep: int = self.env.NUMBER_OF_BACKUPS_TO_KEEP
        if backups_to_keep <= 0 or str(self.env.USE_DEST_DATE_FOLDER).lower() != "true":
            return

        if base_dest_dir.is_symlink() or not base_dest_dir.is_dir():
            self.log_this(f"Retention policy: destination '{base_dest_dir}' is not a directory; skipping", "DEBUG")
            return

        min_backups_to_keep: int = self.env.MIN_BACKUPS_TO_KEEP
        if min_backups_to_keep > 0 and min_backups_to_keep > backups_to_keep:
            self.log_this(
                f"Retention policy: MIN_BACKUPS_TO_KEEP ({min_backups_to_keep}) overrides "
                f"NUMBER_OF_BACKUPS_TO_KEEP ({backups_to_keep})",
                "DEBUG",
            )
            backups_to_keep = min_backups_to_keep

        is_dry_run: bool = self.env.RETENTION_DRY_RUN
        date_format: str = self.env.DEST_DATE_FORMAT
        log_tag: str = " (DRY RUN)" if is_dry_run else ""

        def _parse_date(folder_name: str) -> Optional[datetime]:
            """Return a datetime if folder_name matches date_format, otherwise None."""
            try:
                return datetime.strptime(folder_name, date_format)
            except ValueError:
                return None

        def _record_retention_error(message: str, error: OSError) -> None:
            """Record retention failures without aborting the completed backup."""
            log_message = f"Retention policy: {message}: {error}"
            self._record_error(log_message)
            self.log_this(log_message, "ERROR")

        def _iter_child_dirs(parent: Path) -> List[Path]:
            """Return real child directories, skipping symlinks to avoid pruning outside the destination."""
            try:
                return [child for child in parent.iterdir() if not child.is_symlink() and child.is_dir()]
            except OSError as error:
                _record_retention_error(f"unable to inspect '{parent}'", error)
                return []

        def _log_and_delete(target_folder: Path) -> None:
            """Log and conditionally delete a single backup folder."""
            if is_dry_run:
                self.log_this(f"Retention policy (DRY RUN): would remove '{target_folder}'", "INFO")
            else:
                self.log_this(f"Retention policy: removing '{target_folder}'", "INFO")
                try:
                    shutil.rmtree(target_folder)
                except OSError as error:
                    _record_retention_error(f"failed to remove '{target_folder}'", error)

        def _log_retention_summary(
            container_name: str,
            date_label_newest: str,
            date_label_oldest_kept: str,
            num_kept: int,
            num_to_delete: int,
            kept_date_labels: str,
        ) -> None:
            """Emit the per-container retention summary at DEBUG/TRACE."""
            self.log_this(
                f"Retention policy{log_tag}: '{container_name}' keeping {num_kept} backup(s) "
                f"({date_label_oldest_kept} to {date_label_newest}), {num_to_delete} older backup(s) will be removed",
                "DEBUG",
            )
            self.log_this(f"Retention policy{log_tag}: keeping '{container_name}' in: {kept_date_labels}", "TRACE")

        def _prune_container_date(container_dir: Path) -> None:
            """Prune date folders inside a single container directory (container/date layout)."""
            if container_dir.is_symlink() or not container_dir.is_dir():
                return

            # Collect all date-named subfolders for this container
            dated_backups: List[Tuple[datetime, Path]] = []
            for date_folder in _iter_child_dirs(container_dir):
                parsed_date = _parse_date(date_folder.name)
                if parsed_date is not None:
                    dated_backups.append((parsed_date, date_folder))

            dated_backups.sort(key=lambda entry: entry[0], reverse=True)  # newest first
            backups_kept = dated_backups[:backups_to_keep]
            backups_to_remove = dated_backups[backups_to_keep:]

            if not backups_kept and not backups_to_remove:
                return

            if backups_kept:
                date_label_newest = backups_kept[0][1].name
                date_label_oldest_kept = backups_kept[-1][1].name
                kept_date_labels = ", ".join(folder.name for _, folder in backups_kept)
                _log_retention_summary(
                    container_dir.name,
                    date_label_newest,
                    date_label_oldest_kept,
                    len(backups_kept),
                    len(backups_to_remove),
                    kept_date_labels,
                )

            for _, backup_folder in backups_to_remove:
                _log_and_delete(backup_folder)

        def _prune_date_container(destination_dir: Path) -> None:
            """Prune dated backup folders (date/container layout).

            Treats each date folder as the atomic unit of retention. The N most
            recent date folders are kept; all older ones are removed entirely.
            """
            if destination_dir.is_symlink() or not destination_dir.is_dir():
                return

            dated_folders: List[Tuple[datetime, Path]] = []
            for entry in _iter_child_dirs(destination_dir):
                parsed_date = _parse_date(entry.name)
                if parsed_date is not None:
                    dated_folders.append((parsed_date, entry))

            if not dated_folders:
                return

            dated_folders.sort(key=lambda e: e[0], reverse=True)  # newest first
            folders_kept = dated_folders[:backups_to_keep]
            folders_to_remove = dated_folders[backups_to_keep:]

            if folders_kept:
                date_label_newest = folders_kept[0][1].name
                date_label_oldest_kept = folders_kept[-1][1].name
                kept_labels = ", ".join(f.name for _, f in folders_kept)
                self.log_this(
                    f"Retention policy{log_tag}: keeping {len(folders_kept)} date folder(s) "
                    f"({date_label_oldest_kept} to {date_label_newest}), "
                    f"{len(folders_to_remove)} older folder(s) will be removed",
                    "DEBUG",
                )
                self.log_this(f"Retention policy{log_tag}: keeping: {kept_labels}", "TRACE")

            for _, folder in folders_to_remove:
                _log_and_delete(folder)

        if self.env.DEST_DATE_PATH_FORMAT == "container/date":
            for container_dir in _iter_child_dirs(base_dest_dir):
                _prune_container_date(container_dir)
        elif self.env.DEST_DATE_PATH_FORMAT == "date/container":
            _prune_date_container(base_dest_dir)
        else:
            self.log_this(
                f"Unknown DEST_DATE_PATH_FORMAT '{self.env.DEST_DATE_PATH_FORMAT}' for retention policy", "ERROR"
            )

    def reset_db(self) -> None:
        """Reset the database values to their defaults"""
        self.db.put("containers_completed", 0)
        self.db.put("containers_skipped", 0)
        self.db.put("errors", 0)
        self.db.put("last_backup_seconds_taken", 0)
        self.db.put("last_cron", "None")
        self.db.put("completed", "0")
        self.db.put("backup_running", False)

    def backup(self):
        if self.env.REPORT_FILE == True:
            self.logger._create_new_report_file()

        self.log_this("Starting backup...", "INFO")

        self._reset_outcomes()
        self.reset_db()
        self.db.put("backup_running", True)

        self.start_time = datetime.now()
        self.db.put("last_cron", self.start_time.strftime("%m/%d/%y %H:%M"))

        self._run_exec(None, BeforeAfterorDuring.BEFORE, attached_to_container=False)

        dest_dirs = copy.deepcopy(self.env.SECONDARY_DEST_DIRS)
        for dir in dest_dirs:
            self.log_this(f"Secondary destination directories '{dir.absolute()}'", "DEBUG")
        dest_dirs.insert(0, Path(self.env.DEST_LOCATION))

        for dir in dest_dirs:
            self._backup_additional_folders_standalone(BeforeOrAfter.BEFORE, dir)

        containers_by_group = self.group_containers()

        for group, containers in containers_by_group.items():
            # No need to print group for individual containers
            if not group.startswith(self.default_group_pfx_sfx) and not group.endswith(self.default_group_pfx_sfx):
                self.log_this(f"Backing up group: {group}")

            # Before backup
            for c in containers:
                # Run before hooks
                self._run_exec(c, BeforeAfterorDuring.BEFORE, attached_to_container=True)
                self._run_lifecyle_hook(c, BeforeOrAfter.BEFORE)

                additional_folders_when = str(self.get_label(c, "additional-folders.when", "during")).lower()
                if additional_folders_when == "before":
                    for dir in dest_dirs:
                        self._backup_additional_folders(c, dir)

                label_src_dirs = self._get_label_src_dirs(c)
                any_src_exists = any(src_dir.exists() for src_dir, _ in label_src_dirs)
                if not any_src_exists:
                    src_dir_required = str(self.get_label(c, "source-dir-required", "true")).lower()
                    if src_dir_required == "false":
                        self.log_this(f"{c.name} - Source directory does not exist, but that's okay", "DEBUG")
                    else:
                        self._record_container_skipped(
                            c,
                            "source_directory_missing",
                            f"{c.name} - Source directory does not exist. Skipping",
                            level="WARN",
                        )
                        continue

                stop_result = self._stop_container(c)  # Stop containers
                if not stop_result:
                    self._record_container_failed(
                        c,
                        "stop_failed",
                        f"Error stopping container {c.name}. Skipping backup for this container.",
                        log=False,
                    )

            # During backup
            for c in containers:
                # Backup containers
                c.reload()  # Refresh the status for this container
                if c.status != "exited":
                    stop_before_backup = str(self.get_label(c, "stop-before-backup", "true"))

                    # Allow the user to skip stopping the container before backup
                    # Here we allow the Enviorment variable to supercede the EMPTY label
                    stop_before_backup_env = True
                    SKIP_STOPPING = self.env.SKIP_STOPPING
                    skip_stopping_set = set(SKIP_STOPPING.split(","))
                    if c.name in skip_stopping_set or c.id in skip_stopping_set:
                        stop_before_backup_env = False

                    if stop_before_backup.lower() == "true" and stop_before_backup_env == True:
                        if c.name not in self.containers_skipped:
                            self._record_container_skipped(
                                c,
                                "not_stopped",
                                f"Skipping backup of {c.name} because it was not stopped",
                                level="WARN",
                            )
                        else:
                            self._record_container_skipped(
                                c, "not_stopped", f"Skipping backup of {c.name} because it was not stopped", log=False
                            )
                        continue

                self._backup_container_folders(c)
                secondary_dest_dirs = self.env.SECONDARY_DEST_DIRS

                for dir in secondary_dest_dirs:
                    self._backup_container_folders(c, dir)

                self._run_exec(c, BeforeAfterorDuring.DURING, attached_to_container=True)

            # After backup
            for c in containers:

                start_result = self._start_container(c)  # Start containers
                if not start_result:
                    self._record_container_failed(c, "start_failed", f"Error starting container {c.name}.", log=False)

                self._run_lifecyle_hook(c, BeforeOrAfter.AFTER)
                self._run_exec(c, BeforeAfterorDuring.AFTER, attached_to_container=True)

                additional_folders_when = str(self.get_label(c, "additional-folders.when", "during")).lower()
                if additional_folders_when == "after":
                    for dir in dest_dirs:
                        self._backup_additional_folders(c, dir)

                if c.name not in self.containers_skipped and c.name not in self.containers_failed:
                    self.containers_completed.add(c.name)
                    self.log_this(f"Backup of {c.name} complete!", "INFO")
                elif c.name in self.containers_failed and c.name not in self.containers_skipped:
                    self.log_this(
                        f"Backup data for {c.name} was completed, but the container failed to restart within the start timeout.",
                        "WARN",
                    )

        for dir in dest_dirs:
            self._backup_additional_folders_standalone(BeforeOrAfter.AFTER, dir)

        self._apply_retention_policy(Path(self.env.DEST_LOCATION))
        if self.env.RETENTION_SECONDARY_DESTINATIONS:
            for dir in self.env.SECONDARY_DEST_DIRS:
                self._apply_retention_policy(dir)

        self.end_time = datetime.now()
        exeuction_time = self.end_time - self.start_time
        duration = datetime.fromtimestamp(exeuction_time.total_seconds())

        self.db.put("backup_running", False)
        self.db.put("containers_completed", len(self.containers_completed))
        self.db.put("containers_skipped", len(self.containers_skipped))
        self.db.put("errors", len(self.error_messages))
        self.db.put("last_backup_seconds_taken", round(exeuction_time.total_seconds()))

        self._run_exec(None, BeforeAfterorDuring.AFTER, attached_to_container=False)

        self.log_this("Containers completed: " + self.logger.set_to_string(self.containers_completed), "DEBUG")
        self.log_this("Containers skipped: " + self.logger.set_to_string(self.containers_skipped), "DEBUG")
        if self.containers_skipped:
            skipped_names = self.logger.set_to_string(self.containers_skipped)
            self.log_this(
                f"Skipped {len(self.containers_skipped)} containers: {skipped_names}",
                "INFO",
            )
        if self.containers_failed:
            self.log_this(
                f"Failed {len(self.containers_failed)} containers: {self.logger.set_to_string(self.containers_failed)}",
                "ERROR",
            )
        self.log_this(f"Completed in {duration.strftime('%Mm %Ss')}", "INFO")

        self.log_this(
            f"Success. {len(self.containers_completed)} containers backed up! {len(self.containers_skipped)} skipped.",
            "INFO",
        )

        if self.env.RUN_ONCE == True:
            self.log_this("RUN_ONCE is true. Exiting...", "INFO")
            subprocess.run("kill -SIGTERM 1", shell=True)  # Quit the container
            sys.exit(0)


if __name__ == "__main__":
    try:
        docker_client = docker.from_env()
        docker_client.ping()  # Test connection to Docker
    except Exception as e:
        print(f"Error connecting to Docker. Please either mount the Docker socket or set DOCKER_HOST.")
        exit(1)

    nautical = NauticalBackup(docker_client)
    nautical.backup()
