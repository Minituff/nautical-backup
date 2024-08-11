#!/usr/bin/env python3

import os
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

        if self.env.REPORT_FILE == True and self.env.REPORT_FILE_ON_BACKUP_ONLY == False:
            self.logger._create_new_report_file()

        self.verify_source_location(self.env.SOURCE_LOCATION)
        self.verify_destination_location(self.env.DEST_LOCATION)

    def log_this(self, log_message, log_priority="INFO", log_type=LogType.DEFAULT) -> None:
        """Wrapper for log this"""
        return self.logger.log_this(log_message, log_priority, log_type)

    def verify_source_location(self, src_dir: str):
        self.log_this(f"Verifying source directory '{src_dir}'...", "DEBUG", LogType.INIT)
        if not os.path.isdir(src_dir):
            self.log_this(f"Source directory '{src_dir}' does not exist.", "ERROR", LogType.INIT)
            raise FileNotFoundError(f"Source directory '{src_dir}' does not exist.")
        elif not os.access(src_dir, os.R_OK):
            self.log_this(f"No read access to source directory '{src_dir}'.", "ERROR", LogType.INIT)
            raise PermissionError(f"No read access to source directory '{src_dir}'")

        self.log_this(f"Source directory '{src_dir}' READ access verified", "TRACE", LogType.INIT)

    def verify_destination_location(self, dest_dir: str):
        self.log_this(f"Verifying destination directory '{dest_dir}'...", "DEBUG", LogType.INIT)
        if not os.path.isdir(dest_dir):
            self.log_this(f"Destination directory '{dest_dir}' does not exist.", "ERROR", LogType.INIT)
            raise FileNotFoundError(f"Destination directory '{dest_dir}' does not exist.")
        elif not os.access(dest_dir, os.R_OK):
            self.log_this(f"No read access to destination directory '{dest_dir}'.", "ERROR", LogType.INIT)
            raise PermissionError(f"No read access to destination directory '{dest_dir}'")
        elif not os.access(dest_dir, os.W_OK):
            self.log_this(f"No write access to destination directory '{dest_dir}'.", "ERROR", LogType.INIT)
            raise PermissionError(f"No write access to destination directory '{dest_dir}'")

        self.log_this(f"Destination directory '{dest_dir}' READ/WRITE access verified", "TRACE", LogType.INIT)

    def _should_skip_container(self, c: Container) -> bool:
        """Use logic to determine if a container should be skipped by nautical completely"""

        # Skip self
        SELF_CONTAINER_ID = self.env.SELF_CONTAINER_ID

        try:
            name = c.name
            c_id = c.id
            c_image = c.image
        except ImageNotFound as e:
            self.log_this(f"Skipping container because it's image was not found.", "TRACE")
            return True

        if "minituff/nautical-backup" in str(c.image):
            self.log_this(f"Skipping {c.name} {c.id} because it's image matches 'minituff/nautical-backup'.", "TRACE")
        if c.labels.get("org.opencontainers.image.title") == "nautical-backup":
            self.log_this(f"Skipping {c.name} {c.id} because it's image matches 'nautical-backup'.", "TRACE")
        if c.id == SELF_CONTAINER_ID:
            self.log_this(f"Skipping {c.name} {c.id} because it's ID is the same as Nautical", "TRACE")
            return True
        if c.name == SELF_CONTAINER_ID:
            self.log_this(f"Skipping {c.name} because it's ID is the same as Nautical", "TRACE")
            return True

        # Read the environment variables
        SKIP_CONTAINERS = self.env.SKIP_CONTAINERS

        # Convert the strings into lists
        skip_containers_set = set(SKIP_CONTAINERS.split(","))

        nautical_backup_enable_str = str(c.labels.get("nautical-backup.enable", ""))
        if nautical_backup_enable_str.lower() == "false":
            nautical_backup_enable = False
        elif nautical_backup_enable_str.lower() == "true":
            nautical_backup_enable = True
        else:
            nautical_backup_enable = None

        if nautical_backup_enable == False:
            self.log_this(f"Skipping {c.name} based on label", "DEBUG")
            return True

        if self.env.REQUIRE_LABEL == True and nautical_backup_enable is not True:
            self.log_this(
                f"Skipping {c.name} as 'nautical-backup.enable=true' was not found and REQUIRE_LABEL is true.", "DEBUG"
            )
            return True

        if c.name in skip_containers_set:
            self.log_this(f"Skipping {c.name} based on name", "DEBUG")
            return True

        if c.id in skip_containers_set:
            self.log_this(f"Skipping {c.name} based on ID {c.id}", "DEBUG")
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
                self.containers_skipped.add(c.name)
                continue  # Skip this container

            # Create a default group, so ungrouped items are not grouped together
            default_group = f"{self.default_group_pfx_sfx}{str(c.id)[0:12]}{self.default_group_pfx_sfx}"
            group = str(c.labels.get("nautical-backup.group", default_group))
            if not group or group == "":
                group = default_group

            # Split the group string into a list of groups by comma
            groups = group.split(",")
            for g in groups:
                # Get priority. Default=100
                priority = int(c.labels.get(f"nautical-backup.group.{g}.priority", 100))

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

    def _set_exec_enviornment_variables(self, vars: Dict[str, str]):
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
                curl_command = str(c.labels.get("nautical-backup.curl.before", ""))
                command = str(c.labels.get("nautical-backup.exec.before", curl_command))

                if curl_command and curl_command != "":
                    self.log_this(
                        "Deprecated: 'nautical-backup.curl.before' has been moved to 'nautical-backup.exec.before'",
                        "WARN",
                    )
                if command and command != "":
                    self.log_this("Running PRE-backup exec command for $name", "DEBUG")
            elif when == BeforeAfterorDuring.DURING:
                curl_command = str(c.labels.get("nautical-backup.curl.during", ""))
                command = str(c.labels.get("nautical-backup.exec.during", curl_command))

                if curl_command and curl_command != "":
                    self.log_this(
                        "Deprecated: 'nautical-backup.curl.during' has been moved to 'nautical-backup.exec.during'",
                        "WARN",
                    )
                if command and command != "":
                    self.log_this("Running DURING-backup exec command for $name", "DEBUG")
            elif when == BeforeAfterorDuring.AFTER:
                curl_command = str(c.labels.get("nautical-backup.curl.after", ""))
                command = str(c.labels.get("nautical-backup.exec.after", curl_command))
                if curl_command and curl_command != "":
                    self.log_this(
                        "Deprecated: 'nautical-backup.curl.after' has been moved to 'nautical-backup.exec.after'",
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
        self._set_exec_enviornment_variables(vars)

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
            command = str(c.labels.get("nautical-backup.lifecycle.before", ""))
            timeout = str(c.labels.get("nautical-backup.lifecycle.before.timeout", "60"))
            if command and command != "":
                self.log_this("Running DURING-backup lifecycle hook for $name", "DEBUG")
        elif when == BeforeOrAfter.AFTER:
            timeout = str(c.labels.get("nautical-backup.lifecycle.after.timeout", "60"))
            command = str(c.labels.get("nautical-backup.lifecycle.after", ""))
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

        stop_before_backup = str(c.labels.get("nautical-backup.stop-before-backup", "true"))
        if stop_before_backup.lower() == "false":
            self.log_this(f"Skipping stopping of {c.name} because of label" "DEBUG")
            return True
        if c.status != "running":
            self.log_this(f"Container {c.name} was not running. No need to stop.", "DEBUG")
            return True

        self.log_this(f"Stopping {c.name}...", "INFO")
        try:
            c.stop(timeout=10)  # * Actually stop the container
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

    def _start_container(self, c: Container, attempt=1) -> bool:
        c.reload()  # Refresh the status for this container

        if c.status != "exited":
            self.log_this(f"Container {c.name} was not stopped. No need to start.", "DEBUG")
            return True

        try:
            self.log_this(f"Starting {c.name}...")
            c.start()  # * Actually stop the container
        except APIError as e:
            self.log_this(f"Error starting container {c.name}.", "ERROR")
            return False

        c.reload()  # Refresh the status for this container

        if c.status == "running":
            return True
        elif attempt <= 3:
            self.log_this(f"Container {c.name} was not in running state. Trying again (Attempt {attempt}/3)", "ERROR")
            self._start_container(c, attempt=attempt + 1)
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

        label_src = str(c.labels.get("nautical-backup.override-source-dir", ""))
        if label_src and label_src != "":
            if log == True:
                self.log_this(f"Overriding source directory for {c.name} to '{label_src}' from label")
            src_dir = base_src_dir / label_src
            src_dir_no_path = label_src

        return src_dir, src_dir_no_path

    def _get_dest_dir(self, c: Container, src_dir_name: str) -> Path:
        base_dest_dir = Path(self.env.DEST_LOCATION)
        dest_dir: Path = base_dest_dir / str(c.name)

        keep_src_dir_name_label = str(c.labels.get("nautical-backup.keep_src_dir_name", "")).lower()

        # This allows the user to set the KEEP_SRC_DIR_NAME environment variable to override the label's default if set
        # But the label will still override the environment variable if set to false/true
        if str(self.env.KEEP_SRC_DIR_NAME).lower() == "" and keep_src_dir_name_label == "":
            keep_src_dir_name_label = "true"

        if str(self.env.KEEP_SRC_DIR_NAME).lower() == "true" and keep_src_dir_name_label != "false":
            dest_dir: Path = base_dest_dir / src_dir_name

        if keep_src_dir_name_label == "true":
            dest_dir: Path = base_dest_dir / src_dir_name

        if str(c.name) in self.env.OVERRIDE_DEST_DIR:
            new_dest_dir = self.env.OVERRIDE_DEST_DIR[str(c.name)]
            dest_dir = base_dest_dir / new_dest_dir
            self.log_this(f"Overriding destination directory for {c.name} to '{new_dest_dir}'")

        dest_dir_name = str(c.name)
        if str(c.id) in self.env.OVERRIDE_DEST_DIR:
            new_dest_dir = self.env.OVERRIDE_DEST_DIR[str(c.id)]
            dest_dir = base_dest_dir / new_dest_dir
            dest_dir_name = new_dest_dir
            self.log_this(f"Overriding destination directory for {c.id} to '{new_dest_dir}'")

        label_dest = str(c.labels.get("nautical-backup.override-destination-dir", ""))
        if label_dest and label_dest != "":
            self.log_this(f"Overriding destination directory for {c.name} to '{label_dest}' from label")
            dest_dir = base_dest_dir / label_dest
            dest_dir_name = label_dest

        if str(self.env.USE_DEST_DATE_FOLDER).lower() == "true":
            # Final name of the actual folder
            time_format = str(time.strftime(self.env.DEST_DATE_FORMAT))

            if str(self.env.DEST_DATE_PATH_FORMAT) == "container/date":
                dest_dir: Path = base_dest_dir / dest_dir_name / time_format
            elif str(self.env.DEST_DATE_PATH_FORMAT) == "date/container":
                dest_dir: Path = base_dest_dir / time_format / dest_dir_name

            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)

        return dest_dir

    def _backup_additional_folders_standalone(self, when: BeforeOrAfter):
        """Backup folders that are not associated with a container."""
        additional_folders = str(self.env.ADDITIONAL_FOLDERS)
        additional_folders_when = str(self.env.ADDITIONAL_FOLDERS_WHEN)

        # Ensure backups is only run when it should be
        if additional_folders_when == "before" and when != BeforeOrAfter.BEFORE:
            return
        if additional_folders_when == "after" and when != BeforeOrAfter.AFTER:
            return

        base_src_dir = Path(self.env.SOURCE_LOCATION)
        base_dest_dir = Path(self.env.DEST_LOCATION)

        rsync_args = self._get_rsync_args(None, log=False)

        for folder in additional_folders.split(","):
            if folder == "":
                continue

            src_dir = base_src_dir / folder
            dest_dir = base_dest_dir / folder
            self.log_this(f"Backing up standalone additional folder '{folder}'")
            self._run_rsync(None, rsync_args, src_dir, dest_dir)

    def _backup_additional_folders(self, c: Container):
        additional_folders = str(c.labels.get("nautical-backup.additional-folders", ""))
        base_src_dir = Path(self.env.SOURCE_LOCATION)
        base_dest_dir = Path(self.env.DEST_LOCATION)

        rsync_args = self._get_rsync_args(c, log=False)

        for folder in additional_folders.split(","):
            if folder == "":
                continue

            src_dir = base_src_dir / folder
            dest_dir = base_dest_dir / folder

            if str(self.env.USE_DEST_DATE_FOLDER).lower() == "true":
                time_format = str(time.strftime(self.env.DEST_DATE_FORMAT))

                if str(self.env.DEST_DATE_PATH_FORMAT) == "container/date":
                    dest_dir: Path = base_dest_dir / folder / time_format
                elif str(self.env.DEST_DATE_PATH_FORMAT) == "date/container":
                    dest_dir: Path = base_dest_dir / time_format / folder

                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir, exist_ok=True)

            self.log_this(f"Backing up additional folder '{folder}' for container {c.name}")
            self._run_rsync(c, rsync_args, src_dir, dest_dir)

    def _backup_container_foldes(self, c: Container):
        src_dir, src_folder_top = self._get_src_dir(c, log=False)

        dest_dir = self._get_dest_dir(c, src_folder_top)
        if not dest_dir.exists():
            self.log_this(f"Destination directory '{dest_dir}' does not exit", "DEBUG")

        if src_dir.exists():
            self.log_this(f"Backing up {c.name}...", "INFO")

            rsync_args = self._get_rsync_args(c)
            self._run_rsync(c, rsync_args, src_dir, dest_dir)
        else:
            self.log_this(f"Source directory {src_dir} does not exist. Skipping", "DEBUG")

        additional_folders_when = str(c.labels.get("nautical-backup.additional-folders.when", "during")).lower()
        if not additional_folders_when or additional_folders_when == "during":
            self._backup_additional_folders(c)

    def _run_rsync(self, c: Optional[Container], rsync_args: str, src_dir: Path, dest_dir: Path):
        src_folder = f"{src_dir.absolute()}/"
        dest_folder = f"{dest_dir.absolute()}/"

        command = f"{rsync_args} {src_folder} {dest_folder}"

        self.log_this(f"RUNNING: 'rsync {command}'", "DEBUG")

        args = command.split()  # Split the command into a list of arguments

        out = subprocess.run(args, shell=True, executable="/usr/bin/rsync", capture_output=False)

    def _get_rsync_args(self, c: Optional[Container], log=False) -> str:
        default_rsync_args = self.env.DEFAULT_RNC_ARGS
        custom_rsync_args = ""
        used_default_args = True

        if str(self.env.USE_DEFAULT_RSYNC_ARGS).lower() == "false":
            if log == True:
                self.log_this(f"Disabling default rsync arguments ({self.env.DEFAULT_RNC_ARGS})", "DEBUG")
            default_rsync_args = ""

        if c:
            use_default_args = str(c.labels.get("nautical-backup.use-default-rsync-args", "")).lower()
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
            custom_rsync_args_label = str(c.labels.get("nautical-backup.rsync-custom-args", ""))
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

    def backup(self):
        if self.env.REPORT_FILE == True:
            self.logger._create_new_report_file()

        self.log_this("Starting backup...", "INFO")

        self.db.put("backup_running", True)
        self.db.put("last_cron", datetime.now().strftime("%m/%d/%y %I:%M"))

        self._run_exec(None, BeforeAfterorDuring.BEFORE, attached_to_container=False)
        self._backup_additional_folders_standalone(BeforeOrAfter.BEFORE)

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

                additional_folders_when = str(c.labels.get("nautical-backup.additional-folders.when", "during")).lower()
                if additional_folders_when == "before":
                    self._backup_additional_folders(c)

                src_dir, src_dir_no_path = self._get_src_dir(c)
                if not src_dir.exists():
                    src_dir_required = str(c.labels.get("nautical-backup.source-dir-required-to-stop", "true")).lower()
                    if src_dir_required == "false":
                        self.log_this(f"{c.name} - Source directory '{src_dir}' does, but that's okay", "DEBUG")

                    self.log_this(f"{c.name} - Source directory '{src_dir}' does not exist. Skipping", "DEBUG")
                    self.containers_skipped.add(c.name)
                    continue

                stop_result = self._stop_container(c)  # Stop containers

            # During backup
            for c in containers:
                # Backup containers
                c.reload()  # Refresh the status for this container
                if c.status != "exited":
                    stop_before_backup = str(c.labels.get("nautical-backup.stop-before-backup", "true"))

                    # Allow the user to skip stopping the container before backup
                    # Here we allow the Enviorment variable to supercede the EMPTY label
                    stop_before_backup_env = True
                    SKIP_STOPPING = self.env.SKIP_STOPPING
                    skip_stopping_set = set(SKIP_STOPPING.split(","))
                    if c.name in skip_stopping_set or c.id in skip_stopping_set:
                        stop_before_backup_env = False

                    if stop_before_backup.lower() == "true" and stop_before_backup_env == True:
                        if c.name not in self.containers_skipped:
                            self.log_this(f"Skipping backup of {c.name} because it was not stopped", "WARN")
                        self.containers_skipped.add(c.name)
                        continue

                self._backup_container_foldes(c)

                self._run_exec(c, BeforeAfterorDuring.DURING, attached_to_container=True)

            # After backup
            for c in containers:

                start_result = self._start_container(c)  # Start containers

                self._run_lifecyle_hook(c, BeforeOrAfter.AFTER)
                self._run_exec(c, BeforeAfterorDuring.AFTER, attached_to_container=True)

                additional_folders_when = str(c.labels.get("nautical-backup.additional-folders.when", "during")).lower()
                if additional_folders_when == "after":
                    self._backup_additional_folders(c)

                if c.name not in self.containers_skipped:
                    self.containers_completed.add(c.name)
                    self.log_this(f"Backup of {c.name} complete!", "INFO")

        self._backup_additional_folders_standalone(BeforeOrAfter.AFTER)
        self._run_exec(None, BeforeAfterorDuring.AFTER, attached_to_container=False)

        self.db.put("backup_running", False)
        self.db.put("containers_completed", len(self.containers_completed))
        self.db.put("containers_skipped", len(self.containers_skipped))

        self.log_this("Containers completed: " + self.logger.set_to_string(self.containers_completed), "DEBUG")
        self.log_this("Containers skipped: " + self.logger.set_to_string(self.containers_skipped), "DEBUG")

        self.log_this(
            f"Success. {len(self.containers_completed)} containers backed up! {len(self.containers_skipped)} skipped.",
            "INFO",
        )

        if self.env.RUN_ONCE == True:
            self.log_this("RUN_ONCE is true. Exiting...", "INFO")
            subprocess.run("kill -SIGTERM 1", shell=True)  # Quit the container
            sys.exit(0)


if __name__ == "__main__":
    docker_client = docker.from_env()
    nautical = NauticalBackup(docker_client)
    nautical.backup()
