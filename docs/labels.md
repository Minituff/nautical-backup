Docker Labels allow us to apply settings to Nautical on a per-container basis. Instead of applying [environment variables](./arguments.md), we can apply the label to the each container separately.

### How to add labels

Here are a few examples of how to add labels to a Docker container.
Remember, these labels can be added to any container <small> (other than Nautical itself).</small>

=== "Docker Compose Example 1"
    ```yaml
    version: '3'
    services:
      # Service config ...
      labels:
        - "nautical-backup.enable=true"
        - "nautical-backup.stop-before-backup=true"
        - "nautical-backup.rsync-custom-args= " # Disable custom rsync args
    ```

=== "Docker Compose Example 2"
    ```yaml
    version: '3'
    services:
      pihole:
        container_name: pihole
        image: pihole/pihole:latest
        ports:
          - "53:53/tcp"
          - "53:53/udp"
          - "80:80/tcp"
        volumes:
          - './etc-pihole:/etc/pihole'
          - './etc-dnsmasq.d:/etc/dnsmasq.d'
        labels:
          - "nautical-backup.enable=true"
          - "nautical-backup.stop-before-backup=true"
    ```

=== "Docker Run Example 1"
    ```bash
    docker run --name example-image \
    -l nautical-backup.enable=true \
    -l nautical-backup.stop-before-backup=true \
    my-image:latest
    ```

=== "Docker Run Example 2"
    ```bash
    docker run -d \
      --name pihole \
      -p 53:53/tcp -p 53:53/udp \
      -p 80:80 \
      -e TZ="America/Chicago" \
      -v "${PIHOLE_BASE}/etc-pihole:/etc/pihole" \
      -v "${PIHOLE_BASE}/etc-dnsmasq.d:/etc/dnsmasq.d" \
      -l nautical-backup.enable=true \
      -l nautical-backup.stop-before-backup=true \
      pihole/pihole:latest
    ```

### Label vs Environment Variable Priority
If a container has an Environment Variable applied as well as a conflicting Label, then:
> The container Label takes priority over the global Nautical environment variable.

## Enable or Disable Nautical
This Docker label can be used to achieve 2 things:

1. Opt a container **OUT** of backup
1. Opt a container **IN** to a backup <small>(with the Nautical [Require Label](./arguments.md#require-label) environment variable set to `true`)</small>

> **Default If Missing**: true <small> (all containers will be enabled, unless [Require Label](./arguments.md#require-label) is set to `true`).</small>

```properties
nautical-backup.enable=true
```

=== "Example 1 (Opt out)"
    !!! note ""
        With the [Require Label](./arguments.md#require-label) environment variable *not set* or set to `false`.
        ```yaml
        services: # Example Service #1 config ...
          labels:
            - "nautical-backup.enable=false"
        ```
        ```yaml
        services: # Example Service #2 config ...
          labels:
            - "nautical-backup.enable=true"
        ```
        ```yaml
        services: # Example Service #3 config ...
          labels: 
            # No labels
        ```
        The results of this configuration would be:

        - [ ] Service 1 - *Skipped* since `nautical-backup.enable` was set to `false`
        - [x] Service 2 - *Backed up* since the label `nautical-backup.enable=true` was present
        - [x] Service 3 - *Backed up* since no `nautical-backup.enable=false` label was found
            - The [Require Label](./arguments.md#require-label) environment variable was either *not set* or set to `false` for this example


=== "Example 2 (Opt in)"
    !!! note ""
        With the [Require Label](./arguments.md#require-label) environment variable set to `true`
        ```yaml title=""
        services: # Example Service #1 config ...
          labels:
            - "nautical-backup.enable=true"
        ```
        ```yaml
        services: # Example Service #2 config ...
          labels:
            - "nautical-backup.enable=false"
        ```
        ```yaml
        services: # Example Service #3 config ...
          labels: 
            # No labels
        ```

        The results of this configuration would be:

        - [x] Service 1 - *Backed up* since the label `nautical-backup.enable=true` was present
        - [ ] Service 2 - *Skipped* since `nautical-backup.enable` was set to `false`
        - [ ] Service 3 - *Skipped* since no `nautical-backup.enable=true` label was found
        
<small>🔄 `nautical-backup.enable=false` is the same action as the [Skip Containers](./arguments.md#skip-containers) variable, but applied only to this container.</small>


## Stop Container Before Backup

With this label set to `false`, the container will not be stopped before performing a backup.

> **Default If Missing**: true <small> (container ^^will^^ be stopped before backup).</small>

```properties
nautical-backup.stop-before-backup=false
```

!!! warning "Not stopping containers can produce *corrupt* backups."
    Containers with databases--particularly SQL--need to be shutdown before backup.

    Only do this on containers you know for certain do not need to be shutdown before backup.

<small>🔄 This is a similar action to the [Skip Stopping Containers](./arguments.md#skip-stopping-containers) variable, but applied only to this container.</small>

## Override Source Directory Name

Changes the source directory name that Nautical will look for.

By default, Nautical will look for the source directory that is the same name as the container name.

> **Default If Missing**: *empty* <small>(use container name)</small>

=== "Example 1"
    ```properties
    nautical-backup.override-source-dir=new_folder_name
    ```

=== "Example 2"
    To backup the container `Pi.Alert`, the source directory name must be named `Pi.Alert`, but we can use the override to allow a backup of the folder named `pialert`.
    ```properties
    nautical-backup.override-source-dir=pialert
    ```

<small>🔄 This is the same action as the [Override Source Directory](./arguments.md#override-source-directory) variable, but applied only to this container.</small>

## Override Destination Directory Name
Changes the destination/output directory name that Nautical will create during backups.

By default, Nautical will create destination directory that is the same name as the container name.

> **Default If Missing**: *empty* <small>(use container name)</small>

```properties
nautical-backup.override-destination-dir=new_folder_name
```

<small>🔄 This is the same action as the [Override Destination Directory](./arguments.md#override-destination-directory) variable, but applied only to this container.</small>

## Mirror Source Directory Name to Destination
Mirror the source folder name to the destination folder name. By default <small>(without any [overrides](#override-source-directory-name))</small>, this means both the `source` and `destination` folder names are the ^^same as the container name^^.

When using a [source directory override](#override-source-directory-name), then the `nautical-backup.keep_src_dir_name=true` setting<small> (which is the default) </small>will mean the destination directory will be the same as the source directory, without using a [destination directory overrides](#override-destination-directory-name).

If a [destination directory override](#override-destination-directory-name) is applied for a container, then the override ^^will^^ be used instead of mirroring the source name, regardless of the `KEEP_SRC_DIR_NAME` setting. 

> **Default If Missing**: true

```properties
nautical-backup.keep_src_dir_name=false
```

<small>🔄 This is the same action as the [Mirror Source Directory Name to Destination](./arguments.md#mirror-source-directory-name-to-destination) variable, but applied only to this container.</small>

## Use Default rsync Arguments
Use the default `rsync` arguments `-raq` <small>(recursive, archive, quiet)</small>

Useful when using [Custom rsync Arguments](#custom-rsync-arguments)

> **Default**: *none* <small>(use global setting)</small>

```properties
nautical-backup.use-default-rsync-args=false
```

!!! note "This label will *override* the global setting applied through [Environment Variables](./arguments.md)"
    * A value of `true` will use the default rsync arguments regardless of the global setting.
    * A value of `false` will ^^**not**^^ use the default rsync arguments regardless of the global setting.
    * Not setting the label value will use the [global setting](./arguments.md#custom-rsync-arguments)

<small>🔄 Not setting a label is the same action as the [Use Default rsync Arguments](./arguments.md#use-default-rsync-arguments) variable, but applied only to this container.</small>

## Custom rsync Arguments
Apply custom `rsync` args <small>(in addition to the [default](#use-default-rsync-arguments) args)</small>

> **Default**: *empty* <small>(use global setting)</small>

```properties
nautical-backup.rsync-custom-args=--exclude='*.log' --exclude='*.txt'
```

!!! note "This label will *override* the global setting applied through [Environment Variables](./arguments.md)"
    * *Any value* will override the global rsync arguments configured through [global settings](./arguments.md#custom-rsync-arguments).
    * A value of <small>(space)</small> `"nautical-backup.rsync-custom-args= "` will ^^cancel^^ any [global setting](./arguments.md#custom-rsync-arguments) for this container only.
    * Not setting the label value will use the [global setting](./arguments.md#custom-rsync-arguments).

<small>🔄 Not setting a label is the same action as the [Custom rsync Arguments](./arguments.md#custom-rsync-arguments) variable, but applied only to this container.</small>