from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Protocol, runtime_checkable

from app.nautical_env import NauticalEnv


def _is_set(val) -> bool:
    if val is None:
        return False
    if isinstance(val, str):
        return val.strip() != "" and val.lower() != "none"
    if isinstance(val, (list, tuple, set, dict)):
        return len(val) > 0
    return True


def _to_bool(val) -> Optional[bool]:
    if val is None:
        return None
    s = str(val).strip().lower()
    if s in ("true", "1", "yes", "y", "on"):
        return True
    if s in ("false", "0", "no", "n", "off"):
        return False
    return None


def _get_label(labels: Dict[str, str], key: str, default=None, prefix: str = "nautical-backup"):
    return labels.get(f"{prefix}.{key}", default)


def _split_csv(val: str) -> List[str]:
    items = []
    for part in str(val or "").split(","):
        p = part.strip()
        if p:
            items.append(p)
    return items


@runtime_checkable
class HasBackup(Protocol):
    @property
    def enabled(self) -> str | bool: ...

    @property
    def require_label(self) -> bool | str: ...

    @property
    def dest_dirs(self) -> List[Path]: ...

    @property
    def stop_before_backup(self) -> str | bool: ...

    @property
    def destination_format(self) -> str: ...


@runtime_checkable
class HasConfig(Protocol):
    @property
    def group(self) -> str: ...

    @property
    def group_priority(self) -> int: ...

    @property
    def additional_folders(self) -> str: ...

    @property
    def additional_folders_when(self) -> str: ...

    @property
    def exec_before(self) -> str: ...

    @property
    def exec_after(self) -> str: ...

    @property
    def exec_during(self) -> str: ...

    @property
    def lifecycle_before(self) -> str: ...

    @property
    def lifecycle_after(self) -> str: ...

    @property
    def lifecycle_before_timeout(self) -> str: ...

    @property
    def lifecycle_after_timeout(self) -> str: ...

    @property
    def rsync_custom_args(self) -> str: ...

    @property
    def use_default_rsync_args(self) -> bool | str: ...


@runtime_checkable
class HasVolumes(Protocol):
    @property
    def none(self) -> bool: ...


@runtime_checkable
class HasContainerConfig(Protocol):
    @property
    def config(self) -> HasConfig: ...

    @property
    def backup(self) -> HasBackup: ...

    @property
    def volumes(self) -> HasVolumes: ...


@dataclass
class EffectiveContainerConfig:
    # Skips and control
    backup_enabled_yaml: Optional[bool] = None
    require_label: bool = False
    label_enable: Optional[bool] = None
    stop_before_backup: bool = True

    # Grouping
    group: str = ""
    group_priority: int = 100

    # Rsync
    use_default_rsync_args: bool = True
    rsync_custom_args: str = ""

    # Additional folders
    additional_folders: List[str] = field(default_factory=list)
    additional_folders_when: str = "during"

    # Hooks
    exec_before: str = ""
    exec_after: str = ""
    exec_during: str = ""
    lifecycle_before: str = ""
    lifecycle_after: str = ""
    lifecycle_before_timeout: str = "60"
    lifecycle_after_timeout: str = "60"

    # Destinations
    dest_dirs: List[Path] = field(default_factory=list)

    # Volumes
    volumes_none: bool = False

    # Optional formatting (future)
    destination_format: str = ""

    @staticmethod
    def resolve(
        cont_cfg: Optional[HasContainerConfig],
        labels: Dict[str, str],
        env: NauticalEnv,
        label_prefix: str = "nautical-backup",
    ) -> "EffectiveContainerConfig":
        eff = EffectiveContainerConfig()

        # YAML shortcuts (may be absent if container not in YAML)
        ycfg = cont_cfg.config if cont_cfg else None
        ybak = cont_cfg.backup if cont_cfg else None
        yvol = cont_cfg.volumes if cont_cfg else None

        # backup.enabled (YAML-only) and require_label
        eff.backup_enabled_yaml = _to_bool(ybak.enabled) if ybak else None
        if ybak and ybak.require_label is not None:
            eff.require_label = bool(_to_bool(ybak.require_label))
        else:
            eff.require_label = bool(_to_bool(env.REQUIRE_LABEL))
        eff.label_enable = _to_bool(_get_label(labels, "enable", None, label_prefix))

        # Stop before backup (YAML > label > default True)
        if ybak and ybak.stop_before_backup is not None and str(ybak.stop_before_backup) != "":
            eff.stop_before_backup = bool(_to_bool(ybak.stop_before_backup))
        else:
            stop_label = _get_label(labels, "stop-before-backup", None, label_prefix)
            eff.stop_before_backup = bool(_to_bool(stop_label)) if stop_label is not None else True

        # Grouping
        eff.group = (
            str(ycfg.group)
            if ycfg and _is_set(ycfg.group)
            else str(_get_label(labels, "group", "", label_prefix) or "")
        )
        eff.group_priority = int(ycfg.group_priority) if ycfg and _is_set(ycfg.group_priority) else 100

        # Rsync args
        if ycfg and ycfg.use_default_rsync_args is not None and str(ycfg.use_default_rsync_args) != "":
            eff.use_default_rsync_args = bool(_to_bool(ycfg.use_default_rsync_args))
        else:
            lbl = _get_label(labels, "use-default-rsync-args", None, label_prefix)
            eff.use_default_rsync_args = (
                bool(_to_bool(lbl))
                if lbl is not None
                else bool(_to_bool(env.USE_DEFAULT_RSYNC_ARGS)) if env.USE_DEFAULT_RSYNC_ARGS is not None else True
            )

        eff.rsync_custom_args = (
            str(ycfg.rsync_custom_args)
            if ycfg and _is_set(ycfg.rsync_custom_args)
            else str(_get_label(labels, "rsync-custom-args", env.RSYNC_CUSTOM_ARGS, label_prefix) or "")
        )

        # Additional folders
        add_folders_yaml = str(ycfg.additional_folders) if ycfg else ""
        add_folders_lbl = str(_get_label(labels, "additional-folders", "", label_prefix) or "")
        add_folders_val = add_folders_yaml if _is_set(add_folders_yaml) else add_folders_lbl
        eff.additional_folders = _split_csv(add_folders_val)

        add_when_yaml = str(ycfg.additional_folders_when) if ycfg else ""
        eff.additional_folders_when = add_when_yaml if _is_set(add_when_yaml) else "during"

        # Exec/lifecycle
        eff.exec_before = str(ycfg.exec_before) if ycfg else ""
        eff.exec_after = str(ycfg.exec_after) if ycfg else ""
        eff.exec_during = str(ycfg.exec_during) if ycfg else ""

        eff.lifecycle_before = str(ycfg.lifecycle_before) if ycfg else ""
        eff.lifecycle_after = str(ycfg.lifecycle_after) if ycfg else ""
        eff.lifecycle_before_timeout = str(ycfg.lifecycle_before_timeout) if ycfg else "60"
        eff.lifecycle_after_timeout = str(ycfg.lifecycle_after_timeout) if ycfg else "60"

        # Destinations
        dest_dirs_yaml = list(ybak.dest_dirs) if ybak and ybak.dest_dirs else []
        eff.dest_dirs = dest_dirs_yaml if dest_dirs_yaml else [Path(env.DEST_LOCATION)]

        # Volumes
        eff.volumes_none = bool(yvol.none) if yvol else False

        # Destination format (optional future usage)
        eff.destination_format = str(ybak.destination_format) if ybak else ""

        return eff
