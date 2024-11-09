from pathlib import Path
from typing import Dict, List
import yaml
from pprint import pprint
from nautical_env import NauticalEnv


from docker.models.containers import Container


class ContainerConfig:
    class Match:
        def __init__(
            self,
            container_name: str | None,
            container_id: str | None,
            container_label: str | None,
            container_image: str | None,
        ) -> None:

            self.container_name = container_name
            self.container_id = container_id
            self.container_label = container_label
            self.container_image = container_image
            # self.container_ip_address = None

            if not container_name and not container_id and not container_label and not container_image:
                raise ValueError(
                    "At least one of the following must be set: container_name, container_id, container_label, container_image"
                )

        def __repr__(self) -> str:
            return str(self.__dict__)

    class Volumes:
        class Volume:
            def __init__(self, source: str, dest: str) -> None:
                self.source = source
                self.dest = dest

            def __repr__(self):
                return str(self.__dict__)

        def __init__(self) -> None:
            self.skip_volumes: List[ContainerConfig.Volumes.Volume] = []
            self.only_volumes: List[ContainerConfig.Volumes.Volume] = []

        def __repr__(self):
            return str(self.__dict__)

    class Config:
        def __init__(self) -> None:
            self.enabled = ""
            self.stop_before_backup = ""

            self.group: str = ""
            self.group_priority: int = 100
            # self.source_dir_required = ""

            self.additional_folders: str = ""
            self.additional_folders_when: str = ""

            # self.override_source_dir = ""
            # self.override_destination_dir = ""
            # self.keep_src_dir_name = ""

            self.exec_before = ""
            self.exec_after = ""
            self.exec_during = ""

            self.lifecycle_before = ""
            self.lifecycle_after = ""
            self.lifecycle_before_timeout: str = "60s"
            self.lifecycle_after_timeout: str = "60s"

            self.rsync_custom_args = ""
            self.use_default_rsync_args = ""

        @staticmethod
        def serialize(config_json: Dict):
            config = ContainerConfig.Config()
            if not config_json:
                return config

            config.enabled = config_json.get("enabled", "")
            config.stop_before_backup = config_json.get("stop_before_backup", "")
            config.group = config_json.get("group", "")
            config.group_priority = config_json.get("group_priority", 100)
            config.additional_folders = config_json.get("additional_folders", "")
            config.additional_folders_when = config_json.get("additional_folders_when", "")
            config.exec_before = config_json.get("exec_before", "")
            config.exec_after = config_json.get("exec_after", "")
            config.exec_during = config_json.get("exec_during", "")
            config.lifecycle_before = config_json.get("lifecycle_before", "")
            config.lifecycle_after = config_json.get("lifecycle_after", "")
            config.lifecycle_before_timeout = config_json.get("lifecycle_before_timeout", "")
            config.lifecycle_after_timeout = config_json.get("lifecycle_after_timeout", "")
            config.rsync_custom_args = config_json.get("rsync_custom_args", "")
            config.use_default_rsync_args = config_json.get("use_default_rsync_args", "")
            return config

        def __repr__(self):
            return str(self.__dict__)

    def __init__(
        self,
        yml_tag_name: str,
        name: str,
        description: str,
        match: Match,
        skip_volumes: List[Volumes.Volume],
        only_volumes: List[Volumes.Volume],
        config: Config,
    ) -> None:
        self.yml_tag_name = yml_tag_name
        self.name = name
        self.description = description
        self.match = match
        self.only_volumes: List[ContainerConfig.Volumes.Volume] = only_volumes
        self.skip_volumes: List[ContainerConfig.Volumes.Volume] = skip_volumes
        self.config = config

    @staticmethod
    def from_yml(yml_tag_name: str, yml_data: Dict) -> "ContainerConfig":

        match_json = yml_data.get("match", {})
        match = ContainerConfig.Match(
            container_name=match_json.get("container_name"),
            container_id=match_json.get("container_id"),
            container_label=match_json.get("container_label"),
            container_image=match_json.get("container_image"),
        )

        volumes_json = yml_data.get("volumes", {"skip_volumes": [], "only_volumes": []})

        def process_volume(volume: str) -> ContainerConfig.Volumes.Volume:
            # Fix splitting issue when volume is not in the format "source:dest"
            if ":" not in volume:
                volume += ":"

            # Check if volume has a read-write or read-only flag
            if volume.count(":") >= 2:
                if volume.endswith(":rw") or volume.endswith(":ro"):
                    volume = volume[:-3]
                else:
                    raise ValueError("Invalid volume format: " + volume)

            src, dest = volume.split(":")
            return ContainerConfig.Volumes.Volume(src, dest)

        skip_volumes = []
        for volume in volumes_json.get("skip_volumes", []):
            skip_volumes.append(process_volume(volume))

        only_volumes = []
        for volume in volumes_json.get("only_volumes", []):
            only_volumes.append(process_volume(volume))

        config = ContainerConfig.Config.serialize(yml_data.get("config", {}))

        return ContainerConfig(
            yml_tag_name=yml_tag_name,
            name=yml_data.get("name", ""),
            description=yml_data.get("description", ""),
            match=match,
            skip_volumes=skip_volumes,
            only_volumes=only_volumes,
            config=config,
        )

    def __repr__(self):
        return str(self.__dict__)


class NauticalContainer(Container):
    def __init__(self, container: Container, container_config: ContainerConfig | None = None) -> None:
        super().__init__()
        self._config: ContainerConfig | None = None

    @classmethod
    def from_container(cls, container: Container, container_config: ContainerConfig) -> "NauticalContainer":
        return cls(container, container_config)

    @property
    def config(self) -> ContainerConfig:
        if not self._config:
            raise ValueError("Container config is not set")
        return self._config


class NauticalConfig:
    class DirectoryMapping:
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

    def __init__(self, nauticalEnv: NauticalEnv, config_path: Path | None) -> None:
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

        self._directory_mappings_list: List[NauticalConfig.DirectoryMapping] = self._directory_mappings_from_yml(
            self.yml
        )
        self.directory_mappings_by_source = self._map_directories_by_source(self._directory_mappings_list)

        self.containers = self._containers_from_yml(self.yml)

    def __repr__(self):
        return str(self.__dict__)

    @staticmethod
    def _containers_from_yml(yml: Dict) -> Dict[str, ContainerConfig]:
        containers = yml.get("containers", [])
        configs = {}
        for container_yml_tag in containers:
            config = ContainerConfig.from_yml(container_yml_tag, containers.get(container_yml_tag))
            configs[container_yml_tag] = config
        return configs

    @staticmethod
    def _directory_mappings_from_yml(yml: Dict) -> List[DirectoryMapping]:
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

            ndm = NauticalConfig.DirectoryMapping(
                name=name,
                host_path=host_path,
                nautical_path=nautical_path,
                description=description,
            )
            result.append(ndm)
        return result

    @staticmethod
    def _map_directories_by_source(mappings: List[DirectoryMapping]):
        """Sort the directory mappings by source, this is the most common query method"""
        result: Dict[str, NauticalConfig.DirectoryMapping] = {}
        for map in mappings:
            result[map.host_path] = map
        return result

    def get_directory_mappings_with_precedence(
        self, source_dir: str | Path, directory_mappings_by_source: Dict | None
    ) -> DirectoryMapping:
        """Return the directory mapping for the given source directory, with the highest precedence (by specificity)"""
        map = directory_mappings_by_source if directory_mappings_by_source else self.directory_mappings_by_source

        source_dir = Path(source_dir) if isinstance(source_dir, str) else source_dir

        src = source_dir
        suffix = ""
        while src != Path("/"):
            if str(src) in map:
                matched_ndm: NauticalConfig.DirectoryMapping = map[str(src)]
                ndm = NauticalConfig.DirectoryMapping(
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
    pprint(config)
