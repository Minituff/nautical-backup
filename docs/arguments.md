Nautical provides configuration in the form of Docker enviornment variables.

See the [Installation section](./installation.md), which contains a few examples of applying envrionment variables.

## Time Zone

Sets the time-zone to be used by the CRON schedule. If this environment variable is not set, Nautical will use the default time zone: `UTC`.
To change the time zone, see this [Wikipedia page](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones), find your location and use the value in `TZ Database Name`, e.g `America/Los_Angeles`.

> **Default**: UTC

```properties
TZ=America/Los_Angeles
```

## CRON Schedule
Allow changing the schedule for when the backup is started.

> **Default**: * 4 * * *

```properties
CRON_SCHEDULE=* 4 * * *
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

## Override Source Directory

> **Default**: *empty*

```properties
OVERRIDE_SOURCE_DIR=example1:example1-new-source-data,ctr2:ctr2-new-source
```
<small> The example above would yield the following results:</small>

| Container Name | Old Source Directory | New Source Directory         |
| -------------- | -------------------- | ---------------------------- |
| example1       | `src/example1`       | `src/example1-new-dest-data` |
| ctr2           | `src/ctr2`           | `src/newdest`                |

## Override Destination Directory

> **Default**: *empty*

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
<br>
<br>