Docker Labels allow us to apply settings to Nautical on a per-container basis. Instead of applying [enviornment variables](./arguments.md), we can apply the label to the each container seperately.

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

=== "Docker Run Example"
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

### Label vs Enviornment Variable Priority
If a container has an Enviornment Variable applied as well as a conflicting Label, then:
> The continer Label takes priority over the global Natical enviornment variable.

## Enable Nautical
With the [Require Label](./arguments.md#require-label) enviornment variable set to `true`, then all containers will be skipped unless they have this label.

> **Default If Missing**: true

```properties
nautical-backup.enable=false
```

If the [Require Label](./arguments.md#require-label) enviornment variable is *missing* or set to `false`, then [this label](#enable-nautical) will not be needed since the container will be backed up anyway.

## Skip
Skip any containers completely if this label is present.

> **Default If Missing**: false

```properties
nautical-backup.skip=true
```

<small>🔄 This is the same action as the [Skip Containers](./arguments.md#skip-containers) variable, but applied only to this container.</small>

## Stop Before Backup

With this label applied, the container will not be stopped before performing a backup.

> **Default If Missing**: false

```properties
nautical-backup.stop-before-backup=true
```

!!! warning "Not stoppping containers can produce *corrupt* backups."
    Containers with databases--particularly SQL--need to be shutdown before backup.

    Only do this on containers you know for certain do not need to be shutdown before backup.

<small>🔄 This is the same action [Skip Stopping Containers](./arguments.md#skip-stopping-containers) variable, but applied only to this container.</small>

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