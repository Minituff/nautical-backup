from pathlib import Path
from typing import Dict, List
from enum import Enum

from docker.models.containers import Container


class ContainerConfig:
    """The configuration from the YAML file"""

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

            self.allow_src: List[str] = []
            self.allow_dest: List[str] = []
            self.skip_if_host_path_starts_with: List[str] = []
            self.skip_if_nautical_path_starts_with: List[str] = []

        def __repr__(self):
            return str(self.__dict__)

    class Backup:
        def __init__(self) -> None:
            self.enabled = ""
            self.stop_before_backup = ""
            self.require_label: bool = False
            self.destination_format: str = ""
            self.zip: bool = True  # Can be set globally, or override per-container or per-volume
            self.restore_map: bool = True  # Nautical-manifest file for restoration (future planned)
            self.dest_dirs: List[Path] = []  # Directories where the containers will be backup to

        def __repr__(self):
            return str(self.__dict__)

        @staticmethod
        def serialize(backup_json: Dict) -> "ContainerConfig.Backup":
            backup = ContainerConfig.Backup()
            if not backup_json:
                return backup

            backup.enabled = backup_json.get("enabled", "")
            backup.stop_before_backup = backup_json.get("stop_before_backup", "")
            backup.destination_format = backup_json.get("destination_format", "")
            backup.zip = backup_json.get("zip", True)
            backup.restore_map = backup_json.get("restore_map", True)
            backup.dest_dirs = [Path(dir) for dir in backup_json.get("dest_dirs", [])]
            backup.require_label = backup_json.get("require_label", True)

            return backup

    class Config:
        def __init__(self) -> None:
            self.enabled = ""

            self.group: str = ""
            self.group_priority: int = 100

            self.additional_folders: str = ""
            self.additional_folders_when: str = ""

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
        as_dict: dict,
        name: str,
        description: str,
        match: Match | None,
        allow_src: List[str],
        allow_dest: List[str],
        deny_src: List[str],
        deny_dest: List[str],
        config: Config,
        backup: Backup,
    ) -> None:
        self.as_dict: Dict = as_dict
        self.yml_tag_name = yml_tag_name
        self.name = name
        self.description = description
        self.match = match
        self.allow_src: List[str] = allow_src
        self.allow_dest: List[str] = allow_dest
        self.deny_src: List[str] = deny_src
        self.deny_dest: List[str] = deny_dest
        self.config = config
        self.backup = backup

    # TODO: WAant all the values loaded in the default and overwritten if needed
    @staticmethod
    def from_yml(yml_tag_name: str, yml_data: Dict, default_config=False) -> "ContainerConfig":

        match: ContainerConfig.Match | None = None
        if not default_config:
            match_json = yml_data.get("match", {})
            match = ContainerConfig.Match(
                container_name=match_json.get("container_name"),
                container_id=match_json.get("container_id"),
                container_label=match_json.get("container_label"),
                container_image=match_json.get("container_image"),
            )

        volumes_json = yml_data.get("volumes", {})
        filters_json = volumes_json.get("filters", {}) if volumes_json else {}

        config = ContainerConfig.Config.serialize(yml_data.get("config", {}))
        backup = ContainerConfig.Backup.serialize(yml_data.get("backup", {}))

        return ContainerConfig(
            yml_tag_name=yml_tag_name,
            as_dict=yml_data,
            name=yml_data.get("name", ""),
            description=yml_data.get("description", ""),
            match=match,
            config=config,
            backup=backup,
            allow_src=list(filters_json.get("allow_src", [])),
            allow_dest=list(filters_json.get("allow_dest", [])),
            deny_src=list(filters_json.get("deny_src", [])),
            deny_dest=list(filters_json.get("deny_dest", [])),
        )

    def __repr__(self):
        return str(self.__dict__)

    @staticmethod
    def merge_defaults(base: dict, override: dict):
        """
        Recursively merges 'override' into 'base'.
        For each key in override:
        - If the value is a dict and the same key in base is also a dict, merge them recursively.
        - Otherwise, override or add the key in base with the override value.
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                # Recursively merge nested dicts
                ContainerConfig.merge_defaults(base[key], value)
            else:
                # Replace or add
                base[key] = value
        return base


class NauticalContainer(Container):
    class MountType(Enum):
        BIND = "bind"
        VOLUME = "volume"

    class MountMode(Enum):
        RO = "ro"  # Read Only
        RW = "rw"  # Read/Write
        Z = "z"  # z is a SELinux (Security-Enhanced Linux) label option. It tells Docker to relabel the volume content for shared access between containers.

    class MountRW(Enum):
        READ_ONLY = False
        READ_WRITE = True

    def __init__(
        self,
        container: Container,
        container_config: ContainerConfig | None = None,
        mounts: list["NauticalContainer.Mount"] | None = None,
    ) -> None:
        self._config: ContainerConfig | None = container_config
        self.mounts: list[NauticalContainer.Mount] = mounts or []
        super().__init__(container.attrs, client=container.client, collection=container.collection)  # type: ignore

    def __repr__(self) -> str:
        return str(
            {
                "Nautical Container Name": super().name,
                "Image": super().image,
            }
        )

    @classmethod
    def from_container(cls, container: Container, container_config: ContainerConfig | None) -> "NauticalContainer":
        mounts = container.attrs.get("Mounts", [])
        volume_mounts = [cls.Mount.from_dict(m) for m in mounts]
        return cls(container, container_config, mounts=volume_mounts)

    @property
    def config(self) -> ContainerConfig:
        return self._config  # type: ignore

    @config.setter
    def config(self, value: ContainerConfig) -> None:
        self._config = value

    class Mount:
        def __init__(
            self,
            destination: str,
            mode: "NauticalContainer.MountMode",
            propagation: str,
            RW: "NauticalContainer.MountRW",
            source: str,
            type: "NauticalContainer.MountType",
        ) -> None:
            self.destination = destination
            self.mode = mode
            self.propagation = propagation
            self.RW = RW  # ReadWrite perms
            self.source = source
            self.type = type

        def __repr__(self) -> str:
            return str(self.to_dict())

        @staticmethod
        def from_dict(data: dict) -> "NauticalContainer.Mount":
            type_enum = NauticalContainer.MountType(data.get("Type", ""))
            rw_enum = (
                NauticalContainer.MountRW.READ_WRITE if data.get("RW", False) else NauticalContainer.MountRW.READ_ONLY
            )

            # Sometimes "mode" is blank. Get the value from RW
            mode_val = data.get("Mode", "")
            if not mode_val:
                mode_val = "rw" if rw_enum == NauticalContainer.MountRW.READ_WRITE else "ro"
            mode_enum = NauticalContainer.MountMode(mode_val)

            return NauticalContainer.Mount(
                destination=data.get("Destination", ""),
                mode=mode_enum,
                propagation=data.get("Propagation", ""),
                RW=rw_enum,
                source=data.get("Source", ""),
                type=type_enum,
            )

        def to_dict(self) -> dict:
            return {
                "Source": self.source,
                "Destination": self.destination,
                "Type": self.type.value,
                "Mode": self.mode.value,
                "RW": self.RW.value,
                "Propagation": self.propagation,
            }
