import os
from pathlib import Path
from typing import Dict, List
from enum import Enum
import re

from docker.models.containers import Container
from app.logger import Logger, LogType, LogLevel
from app.functions.helpers import convert_bytes, get_folder_size, separate_number_and_unit


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
        def __init__(
            self,
            allow_src: List[str],
            allow_dest: List[str],
            deny_src: List[str],
            deny_dest: List[str],
            max_size: str | None = None,
        ) -> None:
            self.max_size: str | None = max_size
            self.allow_src: List[str] = allow_src
            self.allow_dest: List[str] = allow_dest
            self.deny_src: List[str] = deny_src
            self.deny_dest: List[str] = deny_dest

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
        volumes: Volumes,
        filtered_volumes: "List[NauticalContainer.Mount] | None",
        config: Config,
        backup: Backup,
    ) -> None:
        self.as_dict: Dict = as_dict
        self.yml_tag_name = yml_tag_name
        self.name = name
        self.description = description
        self.match = match
        self.volumes = volumes
        self.filtered_volumes = filtered_volumes

        self.config = config
        self.backup = backup

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

        volumes = ContainerConfig.Volumes(
            allow_src=list(filters_json.get("allow_src", [])),
            allow_dest=list(filters_json.get("allow_dest", [])),
            deny_src=list(filters_json.get("deny_src", [])),
            deny_dest=list(filters_json.get("deny_dest", [])),
            max_size=filters_json.get("max_size", None),
        )

        return ContainerConfig(
            yml_tag_name=yml_tag_name,
            as_dict=yml_data,
            name=yml_data.get("name", ""),
            description=yml_data.get("description", ""),
            match=match,
            config=config,
            backup=backup,
            volumes=volumes,
            filtered_volumes=None,
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


class ContainerFunctions:
    def __init__(self) -> None:
        self.logger = Logger()

    def log_this(self, log_message, log_level: LogLevel, log_type=LogType.DEFAULT) -> None:
        """Wrapper for log this"""
        return self.logger.log_this(log_message, log_level, log_type)

    def check_folder_exists(self, path: str, c: NauticalContainer) -> bool:
        """
        Check if the given path exists and is a directory.
        Returns True if it exists and is a directory, False otherwise.
        """
        if not path:
            self.log_this(f"{c.name} - Path is empty or None", LogLevel.WARN)
            return False

        # Check if the path exists and is a directory
        if os.path.isdir(path):
            self.log_this(f"{c.name} - Mount source '{path}' exists and is a directory", LogLevel.TRACE)
            return True

        self.log_this(f"{c.name} - Mount source '{path}' does not exist or is not a directory", LogLevel.WARN)
        return False

    def check_read_access(self, path: str, c: NauticalContainer) -> bool:
        """
        Check if the given path has read access.
        Returns True if readable, False otherwise.
        """
        if not path:
            self.log_this(f"{c.name} - Path is empty or None", LogLevel.WARN)
            return False

        # Check read access
        if os.access(path, os.R_OK):
            self.log_this(f"{c.name} - Read access verified for mount source '{path}'", LogLevel.TRACE)
            return True

        self.log_this(f"{c.name} - Cannot verify read access to mount source '{path}'", LogLevel.WARN)
        return False

    def check_mount_size(self, path, max_size: str | None, c: NauticalContainer) -> bool:
        if max_size is None:
            self.log_this(f"{c.name} - Max size is not set for mount source '{path}'", LogLevel.TRACE)
            return True  # Allow all if max size is not set

        size_in_bytes = get_folder_size(path)
        max_size_as_float, unit = separate_number_and_unit(str(max_size))

        max_size_in_bytes = convert_bytes(max_size_as_float, unit)
        if size_in_bytes > max_size_in_bytes:
            self.log_this(f"{c.name} - Mount source '{path}' exceeds maximum size of {max_size}", LogLevel.WARN)
            return False
        return True

    def process_allow_and_deny_for_mounts(self, c: NauticalContainer) -> List[NauticalContainer.Mount]:
        allow_src = c.config.volumes.allow_src
        deny_src = c.config.volumes.deny_src

        allow_dest = c.config.volumes.allow_dest
        deny_dest = c.config.volumes.deny_dest

        def finalize_folder_validation(path) -> bool:
            if not self.check_folder_exists(path, c):
                return False
            if not self.check_read_access(path, c):
                return False
            if not self.check_mount_size(path, c.config.volumes.max_size, c):
                return False
            return True

        allowed_mounts: List[NauticalContainer.Mount] = []
        for mount in c.mounts:
            self.log_this(f"{c.name} - Processing mount '{mount.source}:{mount.destination}'", LogLevel.TRACE)
            deny_mount = False

            # Regex match
            for denied_dest in deny_dest:
                if re.fullmatch(denied_dest, mount.source):
                    self.log_this(
                        f"{c.name} - Denied mount '{mount.source}' by source regex '{denied_dest}'", LogLevel.DEBUG
                    )
                    deny_mount = True
                    break
            if deny_mount:
                continue  # Skip this mount

            for denied_src in deny_src:
                if re.fullmatch(denied_src, mount.destination):
                    self.log_this(
                        f"{c.name} - Denied mount '{mount.destination}' by destination regex '{denied_src}'",
                        LogLevel.DEBUG,
                    )
                    deny_mount = True
                    break

            if deny_mount:
                continue  # Skip this mount

            allow_mount = False
            for allowed_src in allow_src:
                if re.fullmatch(allowed_src, mount.source):
                    self.log_this(
                        f"{c.name} - Allowed mount '{mount.source}' by source regex '{allowed_src}'", LogLevel.DEBUG
                    )

                    allow_mount = True
                    if not finalize_folder_validation(mount.source):
                        continue
                    allowed_mounts.append(mount)
                    break

            if allow_mount:
                continue  # No need to continue checking destinations

            for allowed_dest in allow_dest:
                if re.fullmatch(allowed_dest, mount.destination):
                    self.log_this(
                        f"{c.name} - Allowed mount '{mount.source}:{mount.destination}' by destination regex '{allowed_dest}'",
                        LogLevel.DEBUG,
                    )

                    allow_mount = True
                    if not finalize_folder_validation(mount.source):
                        continue
                    allowed_mounts.append(mount)
                    break
            if allow_mount:
                continue  # No need to continue checking other mounts

            self.log_this(
                f"{c.name} - Denied mount '{mount.source}:{mount.destination}' because it was not matched in allow list",
                LogLevel.DEBUG,
            )
        print(f"{c.name} - Allowed mounts after processing: {len(allowed_mounts)}")
        return allowed_mounts
