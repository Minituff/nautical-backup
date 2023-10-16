Nautical provides configuration in the form of Docker enviornment variables.

See the [Installation Section](./installation.md), which contains a few examples of applying enviornment variables.

### Enviornment Variable vs Label Priority
If a container has an Enviornment Variable applied as well as a conflicting Label, then:
> The continer Label takes priority over the global Natical enviornment variable.

## Time Zone

Sets the time-zone to be used by the CRON schedule. If this environment variable is not set, Nautical will use the default time-zone: `Etc/UTC`.

To change the time-zone, see this [Wikipedia page](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones), find your location and use the value in `TZ Database Name`, e.g `America/Los_Angeles`.

> **Default**: Etc/UTC

```properties
TZ=America/Los_Angeles
```
To verify the correct time-zone, use the command `docker exec nautical-backup date`

## CRON Schedule
Allow changing the schedule for when the backup is started.

> **Default**: 0 4 * * *

```properties
CRON_SCHEDULE=0 4 * * *
```

## Skip Containers
Tell Nautical to skip backup of containers in this list.

This list can either be the container `name` or full `id`.

> **Default**: *empty*

```properties
SKIP_CONTAINERS=container-name1,container-name2,container-name3
```
```properties
SKIP_CONTAINERS=container-name1,056bd2e970c1338782733fdbf1009c6e158c715d0d105b11de88bd549430e7f5
```
!!! tip "Getting the full container ID"
    Usally, it's easier to just use the `container-name`, but if you need to use the full ID, these commands will help:

    * `docker ps --no-trunc`
    * `docker inspect <container name>`

## Require Label
Require the Docker ^^Label^^ `nautical-backup.enable=true` to be present on *each* contianer or it will be skipped.

> **Default**: false

```properties
REQUIRE_LABEL=true
```

See the [Labels Enable Section](./labels.md#enable-nautical) for more details.

## Override Source Directory
Allows a source directory and container-name that do not match.

> **Default**: *empty*

> **Format**: `<container-name>:<local source folder name>`  <small>(comma seperated for multiple items)</small>

Normally a container is backed up *only* when the `container-name` is the exact same as the `source folder name`.

Example 1:

For example, a container named `Pi.Alert` will be skipped with a source directory name of `pialert`.
To fix this, we can override the source directory name so that it does not need to match the container name.

```properties
OVERRIDE_SOURCE_DIR=Pi.Alert:pialert
```

Example 2:

We can override multiple containers if we seperate them with a comma.
```properties
OVERRIDE_SOURCE_DIR=example1:example1-new-source-data,ctr2:ctr2-new-source
```
<small> The example above would yield the following results:</small>

| Container Name | Old Source Directory | New Source Directory         |
| -------------- | -------------------- | ---------------------------- |
| example1       | `src/example1`       | `src/example1-new-dest-data` |
| ctr2           | `src/ctr2`           | `src/newdest`                |

## Override Destination Directory
Changes the destination backup name to be something other than the container name.

> **Default**: *empty*

> **Format**: `<container-name>:<new destination folder name>`  <small>(comma seperated for multiple items)</small>

Normally, a container is backed to a folder with the ^^same name^^ as the `container-name`. 

Example 1:

For example, let's say we have a container named `Pi.Alert`. By default, the container will be backed up to a folder named `Pi.Alert`.
If we want to change this destination folder name to be `pialert`, we can do that using overrides.

```properties
OVERRIDE_DEST_DIR=Pi.Alert:pialert
```


Example 2:

```properties
OVERRIDE_DEST_DIR=example1:example1-new-dest-data,ctr2:newdest
```

<small> The example above would yield the following results:</small>

| Container Name | Old Destination Directory | New Destination Directory     |
| -------------- | ------------------------- | ----------------------------- |
| example1       | `dest/example1`           | `dest/example1-new-dest-data` |
| ctr2           | `dest/ctr2`               | `dest/newdest`                |


## Report file
Enable or Disable the automatically generated report file.

> **Default**: true

```properties
REPORT_FILE=true
```

## Skip Stopping Containers
Bypass stopping the container before performing a backup. This can be useful for containers with minimal configuration.

> **Default**: *empty*

```properties
SKIP_STOPPING=example1,example2
```
!!! warning "Not stoppping containers can produce *corrupt* backups."
    Containers with databases--particularly SQL--need to be shutdown before backup.

    Only do this on containers you know for certain do not need to be shutdown before backup.

## Backup on Start
Will immediatly perform a backup when the container is started in addition to the CRON sheduled backup.

> **Default**: false

```properties
BACKUP_ON_START=true
```

## Log rsync Commands

Log each `rsync` command to console before running <small>(useful for debugging)</small>

> **Default**: false

```properties
LOG_RSYNC_COMMANDS=true
```
You should see something like this in the Nautical contianer logs:
```console
rsync -ahq --exclude='*.log' --exclude='*.txt' /app/source/watchtower/ /app/destination/watchtower/
```

## Use Default rsync Arguments

Use the default `rsync` arguemnts `-raq` <small>(recursive, archive, quiet)</small>

Useful when using [Custom rsync Arugments](#custom-rsync-arguments)

> **Default**: true

```properties
USE_DEFAULT_RSYNC_ARGS=false
```

## Custom rsync Arguments
Apply custom `rsync` args <small>(in addition to the [default](#use-default-rsync-arguments) args)</small>

> **Default**: *empty*

The `RSYNC_CUSTOM_ARGS` will be inserted after the `$DEFAULT_RSYNC_ARGS` as shown:
```bash
rsync $DEFAULT_RSYNC_ARGS $RSYNC_CUSTOM_ARGS $src_dir/ $dest_dir/
```


There are many `rsync` arguments and customizations that be be used here.

Examples:
```properties
# Don't backup any .log or any .txt files
RSYNC_CUSTOM_ARGS=--exclude='*.log' --exclude='*.txt'
```

<br>
<br>
