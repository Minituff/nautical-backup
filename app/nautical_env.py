import os
from pathlib import Path
from typing import Dict, List


class NauticalEnv:
    def __init__(self) -> None:
        self.SKIP_CONTAINERS = os.environ.get("SKIP_CONTAINERS", "")
        self.SKIP_STOPPING = os.environ.get("SKIP_STOPPING", "")
        self.SELF_CONTAINER_ID = os.environ.get("SELF_CONTAINER_ID", "")

        self.LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
        self.REPORT_FILE_LOG_LEVEL = os.environ.get("REPORT_FILE_LOG_LEVEL", "")
        self.REPORT_FILE_ON_BACKUP_ONLY = os.environ.get("REPORT_FILE_ON_BACKUP_ONLY", "")

        self.DEST_LOCATION = os.environ.get("DEST_LOCATION", "")
        self.SOURCE_LOCATION = os.environ.get("SOURCE_LOCATION", "")

        self.KEEP_SRC_DIR_NAME = os.environ.get("KEEP_SRC_DIR_NAME", "")

        self.OVERRIDE_SOURCE_DIR = self._populate_override_dirs("OVERRIDE_SOURCE_DIR")
        self.OVERRIDE_DEST_DIR = self._populate_override_dirs("OVERRIDE_DEST_DIR")

        self.DEFAULT_RNC_ARGS = "-raq"  # Default
        self.USE_DEFAULT_RSYNC_ARGS = os.environ.get("USE_DEFAULT_RSYNC_ARGS", "")
        self.RSYNC_CUSTOM_ARGS = os.environ.get("RSYNC_CUSTOM_ARGS", "")

        self.REQUIRE_LABEL = False
        if os.environ.get("REQUIRE_LABEL", "False").lower() == "true":
            self.REQUIRE_LABEL = True

        self.NAUTICAL_DB_PATH = os.environ.get("NAUTICAL_DB_PATH", "")

        self.USE_DEST_DATE_FOLDER = os.environ.get("USE_DEST_DATE_FOLDER", "")
        self.DEST_DATE_FORMAT = os.environ.get("DEST_DATE_FORMAT", "%Y-%m-%d")
        self.DEST_DATE_PATH_FORMAT = os.environ.get("DEST_DATE_PATH_FORMAT", "date/container")
        if self.DEST_DATE_PATH_FORMAT not in ["date/container", "container/date"]:
            self.DEST_DATE_PATH_FORMAT = "date/container"  # Set default

        # Not associated with containers
        self.ADDITIONAL_FOLDERS = os.environ.get("ADDITIONAL_FOLDERS", "")
        self.ADDITIONAL_FOLDERS_WHEN = os.environ.get("ADDITIONAL_FOLDERS_WHEN", "before")

        self.SECONDARY_DEST_DIRS: List[Path] = []
        for dir in os.environ.get("SECONDARY_DEST_DIRS", "").split(","):
            if not dir or dir.strip() == "":
                continue
            self.SECONDARY_DEST_DIRS.append(Path(dir.strip()))

        self._PRE_BACKUP_CURL = os.environ.get("PRE_BACKUP_CURL", "")
        self._POST_BACKUP_CURL = os.environ.get("POST_BACKUP_CURL", "")

        # Temporily use the CURL variable
        self.PRE_BACKUP_EXEC = os.environ.get("PRE_BACKUP_EXEC", self._PRE_BACKUP_CURL)
        self.POST_BACKUP_EXEC = os.environ.get("POST_BACKUP_EXEC", self._POST_BACKUP_CURL)

        self.RUN_ONCE = False
        if os.environ.get("RUN_ONCE", "False").lower() == "true":
            self.RUN_ONCE = True

        self.REPORT_FILE = True
        if os.environ.get("REPORT_FILE", "True").lower() == "false":
            self.REPORT_FILE = False

    @staticmethod
    def _populate_override_dirs(env_name: str) -> Dict[str, str]:
        """Translate the Enviornment variable from single string to Python Dict.

        ```
        input="example1:example1-new-source-data,ctr2:ctr2-new-source"

        output = {
            "example1": "example1-new-source-data",
            "ctr2": "ctr2-new-source"
        }
        ```
        """
        raw = str(os.environ.get(env_name, ""))

        result = {}

        if not raw:
            return result

        for pair in raw.split(","):
            split = pair.split(":")
            if len(split) < 2:
                continue

            container_name = str(split[0])
            new_dir = str(split[1])
            result[container_name] = new_dir

        return result
