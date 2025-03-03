Nautical provides configuration in the form of Docker environment variables.

See the [Installation Section](./installation.md), which contains a few examples of applying environment variables.

### Environment Variable vs Label Priority
If a container has an Environment Variable applied as well as a conflicting Label, then:
> The container Label takes priority over the global Nautical environment variable.

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

## Enable/Disable CRON Schedule
Completely disable the recurring backup via a CRON schedule.

This could be useful if you want to run Nautical manually via [Backup On Start](#backup-on-start) or the [Rest API](./rest-api.md).

> **Default**: true <small>(CRON enabled)</small>

```properties
CRON_SCHEDULE_ENABLED=false
```


## Create a Dated Destination Folder
This option will tell Nautical to create a new destination folder on backup.

For example: `/dest_folder/2024-04-05/contianer`

> **Default**: false

```properties
USE_DEST_DATE_FOLDER=true
```

### Destination Folder Format

Use the Python [time.strftime()](https://docs.python.org/3/library/time.html#time.strftime) module to format format the destination folder's name.

> **Default**: %Y-%m-%d <small>(2024-04-05 for example)</small>

> **Format**: Python [time.strftime()](https://docs.python.org/3/library/time.html#time.strftime) format

```properties
DEST_DATE_FORMAT=Nautical_Backup-%Y-%m-%d
```

!!! tip "You are allowed to use almost anything in this field"
    While it may be a intended to use the [date format](https://docs.python.org/3/library/time.html#time.strftime) here, you don't have to.
    You could set this value to `latest backup` or insert addional text around the date format like this: `Nautical Backup - %Y-%m-%d`.
    Use this setting to add a *prefix* and/or *suffix* to the dated folder.

    **NOTE:** Some linux machines may have issues with *spaces* in this field. It is recommended you use *underscores* `_` instead of *spaces* when possible.

### Destination Folder Path
Use this option to designate which path strategy is used when creating a dated destination directory.

* `date/container` = */dest_folder/*`2024-04-05`*/container1*
* `container/date` = */dest_folder/container1/*`2024-04-05`

> **Default**: date/container

> **Options**: `container/date` or `date/container`

```properties
DEST_DATE_PATH_FORMAT=date/container
```

### Container Backup Date vs Nautical Start Date
Use the precise date for formatting the destination folder
When `false`, use the time Nautical started the backup (not when the container was backed up).

> **Default**: false

```properties
USE_CONTAINER_BACKUP_DATE=true
```


???+ example "Understanding `USE_CONTAINER_BACKUP_DATE`."
    Let's say you have the following format: `DEST_DATE_FORMAT=%Y-%m-%d_%H-%M-%S`

    Since the timing is so precise <small>(using seconds)</small> we may get a result like this:
    ```python
    -- src
    |-- 2024-11-24_14-26-43
    |-- 2024-11-24_14-26-44
    |-- 2024-11-24_14-28-10
    ```

    But what we actually want is a result like this:
    ```python
    -- src
    |-- 2024-11-24_14-26-43
    #  (1)
    |-- 2024-11-24_14-28-10
    ```

    1. The folder that was here is now within in `2024-11-24_14-26-43` folder

    By setting `USE_CONTAINER_BACKUP_DATE=false`, then the date used will be the time Nautical actually started, not the time when each container is processed.
    Meaning that even if the containers take a few minutes to backup, the folder format will remain the same for each of them.

## Additional Folders
Allows Nautical to backup folders that are not associated with containers.

The additional folders must either exist or be mounted into the `app/source` folder within Nautical.

> **Default**: *empty* <small>(no additional folders)</small>

> **Format**: `<folder_name>`  <small>(comma separated for multiple items)</small>


```properties
ADDITIONAL_FOLDERS=folder1,folder_name2
```

### When to backup additional folders?

Use this setting to decide if the additional folders are backed up *before* or *after* the containers.

> **Default**: before

> **Options**: before, after

```properties
ADDITIONAL_FOLDERS_WHEN=after
```

???+ example "Additional Folders Example"
    This example shows us how to add two additional folders to our backup that are not associated with a container.
    Here, the *additional* folders will be backed up first, followed by any containers Nautical finds.

    The `additional2` folder already exists within the `/opt/volume-data` so it does not need a mount point.

    ```yaml
    ------8<------ "docker-compose-example-no-tooltips.yml:1:7"
          - /opt/volume-data:/app/source #(4)!
          - /mnt/nfs-share/backups:/app/destination
          - /mnt/additional:/app/source/additional #(1)!
        environment:
          - ADDITIONAL_FOLDERS=additional,additional2 #(2)!
          - ADDITIONAL_FOLDERS_WHEN=before #(3)!
    ```
    
    1. Mount `additional` inside the `/app/source` directory in the container
    2. Tell Nautical to process both the `additional` and `additional2` folders
    3. Tell Nautical *when* to backup the additional folders.
            * `before` is the default
    4. The `additional2` folder already exists within the `/opt/volume-data` so it does not need a mount point.

!!! abstract "If the same folder is named in the [Additional Folders](./labels.md#additional-folders) label and a service env variable--it will be backed up twice."

<small>🔄 This is the same action as the [Additional Folders](./labels.md#additional-folders) label, but applied globally.</small>

### Additional folders date format
To enable the [Dated Destination](#create-a-dated-destination-folder) folder syntax for Global Additional folders <small>(not folders tied to containers)</small>, then use this variable.

> **Default**: false <small>(use the base destination folder)</small>

```properties
ADDITIONAL_FOLDERS_USE_DEST_DATE_FOLDER=true
```
!!! note "The [destination folder format](#destination-folder-format) and [destination folder path](#destination-folder-path) enviornment variables will be respected."

## Secondary Destination Locations
Tell Nautical to backup folders to more destination locations--in addition to the normal destination folder <small>(/app/destination)</small>.

This is a path *inside the Nautical* container.

> **Default**: *empty* <small>(no secondary locations)</small>

> **Format**: `<absolute paths>`  <small>(comma separated for multiple items)</small>

```properties
SECONDARY_DEST_DIRS=/path/one,/path/two
```

=== "Example 1"
    !!! note ""
        Pay attention to the newly added highlighed lines:

        ```yaml hl_lines="10-13"
        ------8<------ "docker-compose-example-no-tooltips.yml:1:7"
              - /opt/volume-data:/app/source
              - /mnt/nfs-share/backups:/app/destination
              - /mnt/nfs-share/destination1:/nautical/destination1 #(1)!
              - /another/path:/nautical/destination2 #(2)!
              environment:
              - SECONDARY_DEST_DIRS=/nautical/destination1,/nautical/destination2 #(3)!
        ```

        1. Mount `/nautical/destination1` directory in the container
        2. Mount `/nautical/destination2` directory in the contianer
        3. Tell Nautical to copy files to these two locations:
            * `/nautical/destination1` which actually goes to `/mnt/nfs-share/destination1` on the host machine
            * `/nautical/destination2` which actually goes to `/another/path` on the host machine

!!! tip "[Additional Folders](#additional-folders) will also be copied to these secondary locations."

## Skip Containers
Tell Nautical to skip backup of containers in this list.

This list can either be the container `name` or full `id`.

> **Default**: *empty* <small>(no skips)</small>

=== "Example 1"
    ```properties
    SKIP_CONTAINERS=container-name1,container-name2,container-name3
    ```

=== "Example 2"
    ```properties
    SKIP_CONTAINERS=container-name1,056bd2e970c1338782733fdbf1009c6e158c715d0d105b11de88bd549430e7f5
    ```

!!! tip "Getting the full container ID"
    Usually, it's easier to just use the `container-name`, but if you need to use the full ID, these commands will help:

    * `docker ps --no-trunc`
    * `docker inspect <container name>`

<small>🔄 This is the same action as the [Disable Nautical](./labels.md#enable-or-disable-nautical) label, but applied globally.</small>

## Require Label
Require the Docker ^^Label^^ `nautical-backup.enable=true` to be present on *each* container or it will be skipped.

> **Default**: false

```properties
REQUIRE_LABEL=true
```

See the [Enable or Disable Nautical](./labels.md#enable-or-disable-nautical) Label Section for more details.

## Multi-Instance Label Prefix
Sometimes, running multiple insances of nautical-backup can enable extra funcunality: such as unique CRON schedules for different containers, etc.

By default, nautical-backup will only scan containers having labels starting with `nautical-backup.*`. To be able to run multiple instances of nautical-backup, you may want to customize the label prefix to avoid colision among instances.

> **Default**: nautical-backup

```yaml
services:
  # Multiple instance of nautical
  nautical-inst1:
    environment:
      - LABEL_PREFIX=nautical-backup.inst1
  nautical-inst2:
    environment:
      - LABEL_PREFIX=nautical-backup.inst2

  # Multi targets
  backuped-inst1:
    labels:
      - nautical-backup.inst1.enable=true
  backuped-inst2:
    labels:
      - nautical-backup.inst2.enable=true
```

## Override Source Directory
Allows a source directory and container-name that do not match.

> **Default**: *empty* <small>(use container name)</small>

> **Format**: `<container-name>:<local source folder name>`  <small>(comma separated for multiple items)</small>

Normally a container is backed up *only* when the `container-name` is the exact same as the `source folder name`.

=== "Example 1"
    !!! note ""
        For example, a container named `Pi.Alert` will be skipped with a source directory name of `pialert`.
        To fix this, we can override the source directory name so that it does not need to match the container name.

        ```properties
        OVERRIDE_SOURCE_DIR=Pi.Alert:pialert
        ```

=== "Example 2"
    !!! note ""
        We can override multiple containers if we separate them with a comma.
        ```properties
        OVERRIDE_SOURCE_DIR=example1:example1-new-source-data,ctr2:ctr2-new-source
        ```
        <small> The example above would yield the following results:</small>

        | Container Name | Old Source Directory | New Source Directory           |
        | -------------- | -------------------- | ------------------------------ |
        | example1       | `src/example1`       | `src/example1-new-source-data` |
        | ctr2           | `src/ctr2`           | `src/ctr2-new-source`          |

=== "Example 3"
    !!! note ""
        We can use a nested folder by simply appending it to the source path
        ```properties
        OVERRIDE_SOURCE_DIR=example1:subfolder/example1
        ```
        <small> The example above would yield the following results:</small>

        | Container Name | Old Source Directory | New Source Directory              |
        | -------------- | -------------------- | --------------------------------- |
        | example1       | `src/example1`       | `src/subfolder/example1`          |

<small>🔄 This is the same action as the [Override Source Directory](./labels.md#override-source-directory-name) label, but applied globally.</small>

## Override Destination Directory
Changes the destination backup name to be something other than the container name.

> **Default**: *empty* <small>(use container name)</small>

> **Format**: `<container-name>:<new destination folder name>`  <small>(comma separated for multiple items)</small>

Normally, a container is backed to a folder with the ^^same name^^ as the `container-name`. 

=== "Example 1"
    !!! note ""
        For example, let's say we have a container named `Pi.Alert`. By default, the container will be backed up to a folder named `Pi.Alert`.
        If we want to change this destination folder name to be `pialert`, we can do that using overrides.

        ```properties
        OVERRIDE_DEST_DIR=Pi.Alert:pialert
        ```


=== "Example 2"
    !!! note ""
        ```properties
        OVERRIDE_DEST_DIR=example1:example1-new-dest-data,ctr2:newdest
        ```

        <small> The example above would yield the following results:</small>

        | Container Name | Old Destination Directory | New Destination Directory     |
        | -------------- | ------------------------- | ----------------------------- |
        | example1       | `dest/example1`           | `dest/example1-new-dest-data` |
        | ctr2           | `dest/ctr2`               | `dest/newdest`                |

<small>🔄 This is the same action as the [Override Destination Directory](./labels.md#override-destination-directory-name) label, but applied globally.</small>


## Execute Commands before or after backup
Execute a command *before* or *after* backing up ^^all^^ the containers. This can be used to alert services before shutdown and/or ensure the services came online correctly.

This command will run before/after the entire backup process is initiated.

> **Default**: *empty* <small>(nothing will be done)</small>

> **FORMAT**: The entirety of a `command`

```properties
PRE_BACKUP_EXEC=/config/prepare-for-backup.sh
POST_BACKUP_EXEC=curl -d "Backup successful 😀" ntfy.sh/mytopic
```

------8<------ "exec_request_example.md"

    Add your script to the enviornment variable
    ```properties
    PRE_BACKUP_EXEC=/config/script.sh
    ```

<small>🔄 This is the same action as the [Execute Commands](./labels.md#execute-commands) label, but applied globally (not per container).</small>

## Report file
Enable or Disable the automatically generated report file.

> **Default**: true

```properties
REPORT_FILE=true
```

## Skip Stopping Containers
Bypass stopping the container before performing a backup. This can be useful for containers with minimal configuration.

> **Default**: *empty* <small>(no containers will be skipped)</small>

```properties
SKIP_STOPPING=example1,example2
```
!!! warning "Not stopping containers can produce *corrupt* backups."
    Containers with databases--particularly SQL--need to be shutdown before backup.

    Only do this on containers you know for certain do not need to be shutdown before backup.


<small>🔄 This is the same action as the [Stop Before Backup](./labels.md#stop-container-before-backup) label, but applied globally.</small>

## Stop Timeout
Nautical will allow the contianer *x* amount of _seconds_ to shutdown gracefully before killing the container.

> **Default**: 10 <small>(seconds)</small>

```properties
STOP_TIMEOUT=10
```

<small>🔄 This is the same action as the [Stop Timeout](./labels.md#stop-timeout) label, but applied globally.</small>

## Backup on Start
Nautical will immediately perform a backup when the container is started in addition to the CRON scheduled backup.

> **Default**: false

```properties
BACKUP_ON_START=true
```

!!! info "The console Nautical backup logs will not be avilable until all the containers have been processed."
    This is due to a [limitation](https://github.com/just-containers/s6-overlay/issues/442#issuecomment-1121687777) in [S6-Overlay](https://github.com/just-containers/s6-overlay).

## Run Once
This variable will tell Nautical to immediately quit after the first backup.
If combined with [Backup on Start](#backup-on-start), Nautical will immediately start a backup, then exit.

> **Default**: false

```properties
RUN_ONCE=true
```

Without [Backup on Start](#backup-on-start), the [CRON Schedule](#cron-schedule) will call the backup and then Nautical will exit.

## Mirror Source Directory Name to Destination
Mirror the source folder name to the destination folder name. 

When using a [source directory override](#override-source-directory), then the `KEEP_SRC_DIR_NAME=true` setting <small> (which is the default) </small>will mean the destination directory will be the same as the source directory, without using a [destination directory override](#override-destination-directory).

If a [destination directory override](#override-destination-directory) is applied for a container, then the override ^^will^^ be used instead of mirroring the source name, regardless of the `KEEP_SRC_DIR_NAME` setting. 

> **Default**: true

```properties
KEEP_SRC_DIR_NAME=false
```

=== "Example 1"
    !!! note ""
        ```properties
        OVERRIDE_SOURCE_DIR=Pi.Alert:pialert
        ```

        Here we override the `source` folder to `Pi.Alert` to `pialert`, and since `KEEP_SRC_DIR_NAME=true` <small> (which is the default) </small> the `destination` folder will also be named `pialert`.

        | Container Name | Source Directory | Destination Directory |
        | -------------- | ---------------- | --------------------- |
        | Pi.Alert       | `src/pialert`    | `destination/pialert` |

=== "Example 2"
    !!! note ""
        ```properties
        KEEP_SRC_DIR_NAME=false
        OVERRIDE_SOURCE_DIR=Pi.Alert:pialert
        ```

        Here we override the `source` folder to `Pi.Alert` to `pialert`, and since `KEEP_SRC_DIR_NAME=false` the `destination` folder will not be mirrored, so the *container-name* `Pi.Alert` will be used.

        | Container Name | Source Directory | Destination Directory  |
        | -------------- | ---------------- | ---------------------- |
        | Pi.Alert       | `src/pialert`    | `destination/Pi.Alert` |

=== "Example 3"
    !!! note ""
        ```properties
        OVERRIDE_SOURCE_DIR=Pi.Alert:pialert
        OVERRIDE_DEST_DIR=Pi.Alert:pialert-backup
        ```

        Here we override the `source` folder to `Pi.Alert` to `pialert`.

        We also override the `destination` folder to `pialert-backup`.

        Since a *destination override* is used, the `KEEP_SRC_DIR_NAME` setting is *not* used for this container.

        | Container Name | Source Directory | Destination Directory        |
        | -------------- | ---------------- | ---------------------------- |
        | Pi.Alert       | `src/Pi.Alert`   | `destination/pialert-backup` |
<small>🔄 This is the same action as the [Mirror Source Directory Name to Destination](./labels.md#mirror-source-directory-name-to-destination) label, but applied globally.</small>

## HTTP REST API
Enable or disable the [Nautical API](./rest-api.md).

> **Default**: true

```properties
HTTP_REST_API_ENABLED=false
```

!!! tip "A quick note"
    A `false` value doesn't completely disable the REST API service--it will only disable the logs stating the API starting.
    
    The REST API is used internally for Docker [Healthchecks](https://docs.docker.com/reference/dockerfile). 
    However, you do not open the port, then all the endpoints will remain unreachable.
    See the [Nautical API](./rest-api.md) section for more information.

### API Username and Password
See [API Section](./rest-api.md) for examples how authenticating to the API.

> **Default Username**: admin

> **Default Password**: admin

> **Format**: string

```properties
HTTP_REST_API_USERNAME=admin
HTTP_REST_API_PASSWORD=password
```

!!! tip "Setting the username and password to `""` will not disable authentication. A login is always required."

## Console Log Level
Set the console log level for the container.

> **Default**: INFO

> **Options**: TRACE, DEBUG, INFO, WARN, ERROR

```properties
LOG_LEVEL=INFO
```

## Report Log Level
Set the log level for the generated report file.
Only used if the report file is [enabled](#report-file).

> **Default**: INFO

> **Options**: TRACE, DEBUG, INFO, WARN, ERROR

```properties
REPORT_FILE_LOG_LEVEL=INFO
```

## Use Report File on Backup Only
With a value of `true`, then the report file will only be created when a backup is performed, not during Nautical initialization.

With a value of `false`, then all logs will also be sent to the report file assuming they are the right [log level](#report-log-level).

> **Default**: true

```properties
REPORT_FILE_ON_BACKUP_ONLY=false
```

## Use Default rsync Arguments

Use the default `rsync` arguments `-raq` <small>(recursive, archive, quiet)</small>

Useful when using [Custom rsync Arguments](#custom-rsync-arguments)

> **Default**: true

```properties
USE_DEFAULT_RSYNC_ARGS=false
```

<small>🔄 This is the same action as the [Use Default rsync Arguments](./labels.md#use-default-rsync-arguments) label, but applied globally.</small>

## Custom rsync Arguments
Apply custom `rsync` args <small>(in addition to the [default](#use-default-rsync-arguments) args)</small>

> **Default**: *empty* <small>(no custom rsync args will be applied)</small>

There are many `rsync` [arguments](https://linux.die.net/man/1/rsync) that be be used here.

???+ example "Custom rsync Arguments Example"
    ```properties
    # Don't backup any .log or any .txt files
    RSYNC_CUSTOM_ARGS=--exclude='*.log' --exclude='*.txt'
    ```

The `RSYNC_CUSTOM_ARGS` will be inserted after the `$DEFAULT_RSYNC_ARGS` as shown:
```bash
rsync $DEFAULT_RSYNC_ARGS $RSYNC_CUSTOM_ARGS $src_dir/ $dest_dir/
```



<small>🔄 This is the same action as the [Custom rsync Arguments](./labels.md#custom-rsync-arguments) label, but applied globally.</small>
<br>
<br>
