# Nautical Backup — User Guide

This guide explains Nautical’s key features and how to use them as a new user. It focuses on what you configure and what to expect, without diving into internal code.

## Configuration Overview

- **Sources**: You can configure Nautical via a YAML file (`config.yml`), container labels, and environment variables.
- **Precedence**: When the same option is configured in multiple places, Nautical applies them in this order:

    1. YAML per-container config <small>(highest)</small>
    2. Docker labels on the container
    3. Global environment variables <small>(lowest)</small>

- **Config path**: Nautical looks for the YAML at `NAUTICAL_CONFIG_PATH` (default `/config/config.yml`).

!!! tip "Prefer YAML for per-container settings; use labels for small tweaks and env vars for global behavior."

## Per‑Container Matching

In `config.yml`, define containers under `containers:` and match by one or more of:

- `match.container_name`
- `match.container_id`
- `match.container_label`
- `match.container_image`

Each container entry provides two main sections:

- `config`: Behavioral options (grouping, exec hooks, additional folders, rsync args).
- `backup`: Backup options (enable/require, dest dirs, stop-before-backup, destination format [planned]).

If a running container doesn’t match any YAML entry, Nautical applies defaults and still considers labels and env vars.

## Directory Mappings

Define host → Nautical path mappings in YAML under `directory.mappings`. During backup of allowed mounts, Nautical:

- Finds the best matching mapping for each mount source (deepest path wins).
- Builds the destination path as `<dest_dir>/<mapping.nautical_path>/<relative-subpath>`.
- Optionally nests inside a dated folder if enabled.

This gives consistent, readable destination layouts based on your host directory structure.

## Destination Directories

Per-container destination directories can be set in YAML at `containers.*.backup.dest_dirs`.

- If set: backups (both mounts and additional folders) are written to each of these dest dirs.
- If not set: falls back to the global env `DEST_LOCATION`.

Date folders can be enabled globally (env):

- `USE_DEST_DATE_FOLDER=true` creates dated subfolders
- `DEST_DATE_FORMAT` controls the date name (e.g. `%Y-%m-%d`)
- `DEST_DATE_PATH_FORMAT` controls path layout (`date/container` or `container/date`)

## Volumes and Filters

Nautical inspects container mounts and applies filters:

- Allow/Deny by source/destination (regex strings) and an optional `max_size` guard.
- YAML allows `volumes.none: true` to skip mount backups entirely for a container (hooks and additional folders still run).

Only allowed mounts are synchronized.

## Grouping

You can group containers to control backup order and grouping behavior.

- YAML: `containers.*.config.group` and `group_priority`.
- Labels: `nautical-backup.group` and `nautical-backup.group.<name>.priority` as fallback.

If no group is set, Nautical gives the container a unique implicit group so it runs independently.

## Additional Folders

In addition to container mounts, you can back up extra host folders:

- **Global (env)**: `ADDITIONAL_FOLDERS` and `ADDITIONAL_FOLDERS_WHEN` for “standalone” folders.
- **Per-container (YAML)**: `containers.*.config.additional_folders` and `additional_folders_when`.

Per precedence, per-container YAML overrides label values. Global env controls the standalone set.

## Exec and Lifecycle Hooks

You can run commands before, during, and after backups:

- **Per-container (YAML)**: `exec_before`, `exec_during`, `exec_after` and lifecycle hooks `lifecycle_before/after` with timeouts.
- Labels can provide the same values when YAML is not used.
- **Global (env)**: `PRE_BACKUP_EXEC` and `POST_BACKUP_EXEC` run once before/after all containers.

Use hooks to quiesce services, signal maintenance windows, or notify completion.

## rsync Arguments

Nautical uses rsync to copy data.

- Default args are enabled by env (`USE_DEFAULT_RSYNC_ARGS`, default true; args value from `DEFAULT_RNC_ARGS`).
- Per-container YAML can override whether default args are used and can set `rsync_custom_args`.
- Labels can also set `rsync-custom-args` or `use-default-rsync-args` when YAML isn’t used.

## Enable/Require Controls

- **Skip by label**: `nautical-backup.enable=false` always skips a container.
- **YAML control**: `containers.*.backup.enabled=false` also skips a container.
- **Require a label**: If enabled (YAML `backup.require_label` or env `REQUIRE_LABEL`), a container must have `nautical-backup.enable=true` or it’s skipped.

## YAML Schema and Validation

Nautical validates `config.yml` and fails fast with helpful messages when a field is misplaced or typed incorrectly. This helps catch mistakes early.

## Putting It Together

1. Point Nautical to your YAML with `NAUTICAL_CONFIG_PATH` and define your containers and mappings.
1. Set global env vars for dates, logging, and other cross-cutting defaults.
1. Use labels for one-off container tweaks if you don’t want to edit YAML.

When multiple sources set the same option, YAML wins over labels, and labels win over env.

## What’s Next

Planned enhancements (tracked in the project docs) include destination format tokens, optional zipping of backups, restore manifests, and multi-destination strategies. Check release notes for availability.

