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

## Stop Before Backup
Similar to the [Skip Stopping Containers](./arguments.md#skip-stopping-containers) variable. 
With this label applied, the container will not be stopped before performing a backup.

> **Default If Missing**: false

```properties
nautical-backup.stop-before-backup=true
```