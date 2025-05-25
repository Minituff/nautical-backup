from pathlib import Path
from typing import Dict, List
import yaml
from pprint import pprint
from nautical_env import NauticalEnv
from classes.nautical_contianer import ContainerConfig
from classes.jamespath_overrides import JamesPathDictMerger


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

        # Values NOT to get overridden by the DefaultContainerConfig
        self._jamespaths_defaults = {
            "name": "Default Name",
            "match.container_name": "Default Container",
            "match.container_id": None,
            "match.container_label": "N/A",
            "match.container_image": None,
            "description": "Default Description",
        }
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
        self.PRE_BACKUP_EXEC = env.get("PRE_BACKUP_EXEC", nauticalEnv.PRE_BACKUP_EXEC)
        self.POST_BACKUP_EXEC = env.get("POST_BACKUP_EXEC", nauticalEnv.POST_BACKUP_EXEC)

        self.default_container_config = self._load_default_container_config(self.yml)

        self._directory_mappings_list: List[NauticalConfig.DirectoryMapping] = self._directory_mappings_from_yml(
            self.yml
        )
        self.directory_mappings_by_source = self._map_directories_by_source(self._directory_mappings_list)

        self._containers_from_yml_by_tag_name: Dict[str, ContainerConfig] = {}
        self._containers_from_yml_by_id: Dict[str, ContainerConfig] = {}
        self._containers_from_yml_by_name: Dict[str, ContainerConfig] = {}
        self._containers_from_yml_by_image: Dict[str, ContainerConfig] = {}
        self._containers_from_yml_by_label: Dict[str, ContainerConfig] = {}
        self._load_containers_from_yml(self.yml)

    def __repr__(self):
        return str(self.__dict__)

    def print(self):
        pprint(self.__dict__)

    @property
    def containers_from_yml_by_id(self) -> Dict[str, ContainerConfig]:
        return self._containers_from_yml_by_id

    @property
    def containers_from_yml_by_name(self) -> Dict[str, ContainerConfig]:
        return self._containers_from_yml_by_name

    @property
    def containers_from_yml_by_tag_name(self) -> Dict[str, ContainerConfig]:
        return self._containers_from_yml_by_tag_name

    @property
    def containers_from_yml_by_image(self) -> Dict[str, ContainerConfig]:
        return self._containers_from_yml_by_image

    @property
    def containers_from_yml_by_label(self) -> Dict[str, ContainerConfig]:
        return self._containers_from_yml_by_label

    def _load_default_container_config(self, yml: Dict) -> ContainerConfig:
        """Loads the default container configurations from the yml file"""
        default_container_config = yml.get("DEFAULT_CONTAINER_CONFIG", None)

        if default_container_config:
            return ContainerConfig.from_yml(
                "DEFAULT_CONTAINER_CONFIG",
                default_container_config,
                default_config=True,
            )
        else:
            raise ValueError("DEFAULT_CONTAINER_CONFIG not found")

    def _load_containers_from_yml(self, yml: Dict) -> None:
        """Loads the container configurations from the yml file"""
        containers: Dict[str, Dict | None] = yml.get("containers", [])

        for container_yml_tag in containers:
            container_values = containers.get(container_yml_tag)
            if not container_values:
                continue

            merged_config = ContainerConfig.merge_defaults(container_values, self.default_container_config.as_dict)

            # Allow selective overrides using JamesPathDictMerger
            JamesPathDictMerger.selective_override(
                merged_config, self.default_container_config.as_dict, self._jamespaths_defaults
            )
            print(merged_config)
            print("---")
            config = ContainerConfig.from_yml(container_yml_tag, container_values)
            self._containers_from_yml_by_tag_name[container_yml_tag] = config

            value_match = container_values.get("match", {})
            if value_match.get("container_name", None):
                self._containers_from_yml_by_name[value_match.get("container_name")] = config
            if value_match.get("container_id", None):
                self._containers_from_yml_by_id[value_match.get("container_id")] = config
            if value_match.get("container_image", None):
                self._containers_from_yml_by_image[value_match.get("container_image")] = config
            if value_match.get("container_label", None):
                self._containers_from_yml_by_label[value_match.get("container_label")] = config

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
        self,
        source_dir: str | Path,
        directory_mappings_by_source: Dict | None,
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
    # pprint(config.print())
