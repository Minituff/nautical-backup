import os
from pathlib import Path
from typing import Dict, List, Optional
import yaml
from pprint import pprint
from nautical_env import NauticalEnv
import inspect
from copy import deepcopy


class NauticalDirectoryMapping:
    def __init__(
        self, name: str, host_path: str, nautical_path: str, description: str = "", final_path: Path | None = None
    ) -> None:
        self.name = name
        self.host_path = host_path
        self.nautical_path = nautical_path
        self.description = description
        self.final_path = final_path

    def __repr__(self):
        return str(self.__dict__)


class NauticalConfig:
    def __init__(self, nauticalEnv: NauticalEnv, config_path: Optional[Path]) -> None:
        self.nauticalEnv = nauticalEnv
        self.config_path = config_path if config_path else Path(nauticalEnv.NAUTICAL_CONFIG_PATH)
        self.yml = self._load_yaml(config_path)
        env = self.yml.get("env", {})

        # Load the environment variables from config file.
        # If variable is not set, then use the default value from NauticalEnv (Container ENV)

        self.RUN_ONCE = env.get("RUN_ONCE", nauticalEnv.RUN_ONCE)
        self.REPORT_FILE = env.get("REPORT_FILE", nauticalEnv.REPORT_FILE)
        self.LOG_LEVEL = env.get("LOG_LEVEL", nauticalEnv.LOG_LEVEL)
        self.REQUIRE_LABEL = env.get("REQUIRE_LABEL", nauticalEnv.REQUIRE_LABEL)
        self.SKIP_CONTAINERS = env.get("SKIP_CONTAINERS", nauticalEnv.SKIP_CONTAINERS)
        self.SKIP_STOPPING = env.get("SKIP_STOPPING", nauticalEnv.SKIP_STOPPING)
        self.SELF_CONTAINER_ID = env.get("SELF_CONTAINER_ID", nauticalEnv.SELF_CONTAINER_ID)
        self.REPORT_FILE_LOG_LEVEL = env.get("REPORT_FILE_LOG_LEVEL", nauticalEnv.REPORT_FILE_LOG_LEVEL)
        self.REPORT_FILE_ON_BACKUP_ONLY = env.get("REPORT_FILE_ON_BACKUP_ONLY", nauticalEnv.REPORT_FILE_ON_BACKUP_ONLY)
        self.DEST_LOCATION = env.get("DEST_LOCATION", nauticalEnv.DEST_LOCATION)
        self.SOURCE_LOCATION = env.get("SOURCE_LOCATION", nauticalEnv.SOURCE_LOCATION)
        self.KEEP_SRC_DIR_NAME = env.get("KEEP_SRC_DIR_NAME", nauticalEnv.KEEP_SRC_DIR_NAME)
        self.OVERRIDE_SOURCE_DIR = env.get("OVERRIDE_SOURCE_DIR", nauticalEnv.OVERRIDE_SOURCE_DIR)
        self.OVERRIDE_DEST_DIR = env.get("OVERRIDE_DEST_DIR", nauticalEnv.OVERRIDE_DEST_DIR)
        self.DEFAULT_RNC_ARGS = env.get("DEFAULT_RNC_ARGS", nauticalEnv.DEFAULT_RNC_ARGS)
        self.USE_DEFAULT_RSYNC_ARGS = env.get("USE_DEFAULT_RSYNC_ARGS", nauticalEnv.USE_DEFAULT_RSYNC_ARGS)
        self.RSYNC_CUSTOM_ARGS = env.get("RSYNC_CUSTOM_ARGS", nauticalEnv.RSYNC_CUSTOM_ARGS)
        self.USE_DEST_DATE_FOLDER = env.get("USE_DEST_DATE_FOLDER", nauticalEnv.USE_DEST_DATE_FOLDER)
        self.DEST_DATE_FORMAT = env.get("DEST_DATE_FORMAT", nauticalEnv.DEST_DATE_FORMAT)
        self.DEST_DATE_PATH_FORMAT = env.get("DEST_DATE_PATH_FORMAT", nauticalEnv.DEST_DATE_PATH_FORMAT)
        self.ADDITIONAL_FOLDERS = env.get("ADDITIONAL_FOLDERS", nauticalEnv.ADDITIONAL_FOLDERS)
        self.ADDITIONAL_FOLDERS_WHEN = env.get("ADDITIONAL_FOLDERS_WHEN", nauticalEnv.ADDITIONAL_FOLDERS_WHEN)
        self.SECONDARY_DEST_DIRS = env.get("SECONDARY_DEST_DIRS", nauticalEnv.SECONDARY_DEST_DIRS)
        self.PRE_BACKUP_EXEC = env.get("PRE_BACKUP_EXEC", nauticalEnv.PRE_BACKUP_EXEC)
        self.POST_BACKUP_EXEC = env.get("POST_BACKUP_EXEC", nauticalEnv.POST_BACKUP_EXEC)

        self._directory_mappings_list: List[NauticalDirectoryMapping] = self._serialize_directory_mappings(self.yml)
        self.directory_mappings_by_source = self._map_directories_by_source(self._directory_mappings_list)

    @staticmethod
    def _serialize_directory_mappings(yml: Dict) -> List[NauticalDirectoryMapping]:
        mappings = yml.get("directory", {}).get("mappings", {})
        result = []
        for name, data in mappings.items():
            host_path = data.get("host_path", "")
            nautical_path = data.get("nautical_path")
            description = data.get("description", "")

            if not nautical_path:
                raise ValueError(f"'nautical_path' key is missing in directory mapping: {name}")
            if not host_path:
                raise ValueError(f"'host_path' key is missing in directory mapping: {name}")

            ndm = NauticalDirectoryMapping(
                name=name,
                host_path=host_path,
                nautical_path=nautical_path,
                description=description,
            )
            result.append(ndm)
        return result

    @staticmethod
    def _map_directories_by_source(mappings: List[NauticalDirectoryMapping]):
        """Sort the directory mappings by source, this is the most common query method"""
        result: Dict[str, NauticalDirectoryMapping] = {}
        for map in mappings:
            result[map.host_path] = map
        return result

    def get_directory_mappings_with_precedence(
        self, source_dir: str | Path, directory_mappings_by_source: Dict | None
    ) -> NauticalDirectoryMapping:
        """Return the directory mapping for the given source directory, with the highest precedence (by specificity)"""
        map = directory_mappings_by_source if directory_mappings_by_source else self.directory_mappings_by_source

        source_dir = Path(source_dir) if isinstance(source_dir, str) else source_dir

        src = source_dir
        suffix = ""
        while src != Path("/"):
            if str(src) in map:
                matched_ndm: NauticalDirectoryMapping = map[str(src)]
                ndm = NauticalDirectoryMapping(
                    name=matched_ndm.name,
                    host_path=str(src),
                    nautical_path=matched_ndm.nautical_path,
                    description=matched_ndm.description,
                    final_path=Path(matched_ndm.nautical_path) / suffix,
                )
                return ndm

            suffix = src.name + "/" + suffix
            src = src.parent

        raise ValueError(f"Directory mapping not found for source: {source_dir}")

    def __repr__(self):
        repr = inspect.cleandoc(
            f"""
        REPORT_FILE: {self.REPORT_FILE}
        LOG_LEVEL: {self.LOG_LEVEL}
        REQUIRE_LABEL: {self.REQUIRE_LABEL}
        SKIP_CONTAINERS: {self.SKIP_CONTAINERS}
        SKIP_STOPPING: {self.SKIP_STOPPING}
        SELF_CONTAINER_ID: {self.SELF_CONTAINER_ID}
        REPORT_FILE_LOG_LEVEL: {self.REPORT_FILE_LOG_LEVEL}
        REPORT_FILE_ON_BACKUP_ONLY: {self.REPORT_FILE_ON_BACKUP_ONLY}
        DEST_LOCATION: {self.DEST_LOCATION}
        SOURCE_LOCATION: {self.SOURCE_LOCATION}
        KEEP_SRC_DIR_NAME: {self.KEEP_SRC_DIR_NAME}
        OVERRIDE_SOURCE_DIR: {self.OVERRIDE_SOURCE_DIR}
        OVERRIDE_DEST_DIR: {self.OVERRIDE_DEST_DIR}
        DEFAULT_RNC_ARGS: {self.DEFAULT_RNC_ARGS}
        USE_DEFAULT_RSYNC_ARGS: {self.USE_DEFAULT_RSYNC_ARGS}
        RSYNC_CUSTOM_ARGS: {self.RSYNC_CUSTOM_ARGS}
        USE_DEST_DATE_FOLDER: {self.USE_DEST_DATE_FOLDER}
        DEST_DATE_FORMAT: {self.DEST_DATE_FORMAT}
        DEST_DATE_PATH_FORMAT: {self.DEST_DATE_PATH_FORMAT}
        ADDITIONAL_FOLDERS: {self.ADDITIONAL_FOLDERS}
        ADDITIONAL_FOLDERS_WHEN: {self.ADDITIONAL_FOLDERS_WHEN}
        SECONDARY_DEST_DIRS: {self.SECONDARY_DEST_DIRS}
        PRE_BACKUP_EXEC: {self.PRE_BACKUP_EXEC}
        POST_BACKUP_EXEC: {self.POST_BACKUP_EXEC}
        """
        )
        return repr

    @staticmethod
    def _load_yaml(path):
        """Load yaml file"""

        if not path.exists():
            print("Config file does not exist")
            raise FileNotFoundError

        with open(path, "r") as filepath:
            gen = yaml.safe_load_all(filepath)
            starting_dict = next(gen)
            for d in gen:
                starting_dict.update(d)
            return starting_dict
        return None


if __name__ == "__main__":
    config_path = Path("dev/config/config.yml")
    env = NauticalEnv()
    config = NauticalConfig(env, config_path)
    # print(config._directory_mappings_list)
    print(config.get_directory_mappings_with_precedence("/var/lib/docker/volumes/TEST", None))
    # print(config)
