from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class EnvModel(BaseModel):
    RUN_ONCE: Optional[bool] = None
    REPORT_FILE: Optional[bool] = None
    LOG_LEVEL: Optional[str] = None
    REQUIRE_LABEL: Optional[bool] = None
    SKIP_CONTAINERS: Optional[str] = None
    SKIP_STOPPING: Optional[str] = None
    SELF_CONTAINER_ID: Optional[str] = None
    REPORT_FILE_LOG_LEVEL: Optional[str] = None
    REPORT_FILE_ON_BACKUP_ONLY: Optional[bool | str] = None

    DEST_LOCATION: Optional[str] = None
    SOURCE_LOCATION: Optional[str] = None
    KEEP_SRC_DIR_NAME: Optional[bool | str] = None

    OVERRIDE_SOURCE_DIR: Optional[str] = None
    OVERRIDE_DEST_DIR: Optional[str] = None

    DEFAULT_RSYNC_ARGS: Optional[str] = None
    DEFAULT_RNC_ARGS: Optional[str] = None
    USE_DEFAULT_RSYNC_ARGS: Optional[bool | str] = None
    RSYNC_CUSTOM_ARGS: Optional[str] = None

    USE_DEST_DATE_FOLDER: Optional[bool | str] = None
    DEST_DATE_FORMAT: Optional[str] = None
    DEST_DATE_PATH_FORMAT: Optional[str] = None

    ADDITIONAL_FOLDERS: Optional[str] = None
    ADDITIONAL_FOLDERS_WHEN: Optional[str] = None
    ADDITIONAL_FOLDERS_USE_DEST_DATE_FOLDER: Optional[bool | str] = None

    SECONDARY_DEST_DIRS: Optional[str] = None
    PRE_BACKUP_EXEC: Optional[str] = None
    POST_BACKUP_EXEC: Optional[str] = None

    @model_validator(mode="after")
    def validate_date_path_format(self):
        fmt = self.DEST_DATE_PATH_FORMAT
        if fmt and fmt not in ("date/container", "container/date"):
            raise ValueError("DEST_DATE_PATH_FORMAT must be 'date/container' or 'container/date'")
        return self


class FiltersModel(BaseModel):
    allow_src: List[str] = Field(default_factory=list)
    allow_dest: List[str] = Field(default_factory=list)
    deny_src: List[str] = Field(default_factory=list)
    deny_dest: List[str] = Field(default_factory=list)
    # Some configs place max_size under filters; allow either location
    max_size: Optional[str] = None


class VolumesModel(BaseModel):
    # Preferred location for max_size
    max_size: Optional[str] = None
    filters: FiltersModel = Field(default_factory=FiltersModel)
    # Allow disabling volume processing entirely
    none: Optional[bool] = None


class BackupModel(BaseModel):
    enabled: Optional[bool] = None
    require_label: Optional[bool] = None
    destination_format: Optional[str] = None
    zip: Optional[bool] = True
    restore_map: Optional[bool] = True
    dest_dirs: List[Path] = Field(default_factory=list)


class ConfigModel(BaseModel):
    enabled: Optional[bool] = None
    group: Optional[str] = None
    group_priority: int = 100

    additional_folders: Optional[str] = None
    additional_folders_when: Optional[str] = None

    exec_before: Optional[str] = None
    exec_after: Optional[str] = None
    exec_during: Optional[str] = None

    lifecycle_before: Optional[str] = None
    lifecycle_after: Optional[str] = None
    lifecycle_before_timeout: Optional[str] = None
    lifecycle_after_timeout: Optional[str] = None

    rsync_custom_args: Optional[str] = None
    use_default_rsync_args: Optional[bool | str] = None


class MatchModel(BaseModel):
    container_name: Optional[str] = None
    container_id: Optional[str] = None
    container_label: Optional[str] = None
    container_image: Optional[str] = None

    @model_validator(mode="after")
    def at_least_one(self):
        if not any([self.container_name, self.container_id, self.container_label, self.container_image]):
            # Allow empty when used as part of DEFAULT config (which omits match entirely)
            raise ValueError(
                "At least one of match.container_name, match.container_id, match.container_label, match.container_image must be set"
            )
        return self


class ContainerModel(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    match: Optional[MatchModel] = None

    volumes: VolumesModel = Field(default_factory=VolumesModel)
    config: ConfigModel = Field(default_factory=ConfigModel)
    backup: BackupModel = Field(default_factory=BackupModel)


class DirectoryMappingModel(BaseModel):
    host_path: str
    nautical_path: str
    description: Optional[str] = ""


class DirectoryModel(BaseModel):
    mappings: Dict[str, DirectoryMappingModel] = Field(default_factory=dict)


class NauticalConfigModel(BaseModel):
    env: Optional[EnvModel] = None
    DEFAULT_CONTAINER_CONFIG: ContainerModel
    containers: Dict[str, ContainerModel] = Field(default_factory=dict)
    directory: DirectoryModel = Field(default_factory=DirectoryModel)
