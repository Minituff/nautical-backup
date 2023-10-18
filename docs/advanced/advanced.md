These exmaples used Docker Compose syntax. See the [Installation section](../installation.md#docker-compose-example) to fit them into your configuration.

## Alternative Source Directories
Don't have all your container volumes in the same directory? That's okay, we can use Docker volume mappings to help.

!!! tip "Remember the folder naming convention"
    1. The `container-name` must match the `source` and `destination` folder names.
    2. You can override this using [Aruguments](../arguments.md#override-source-directory).

### Sandard and Alternative
```yaml
volumes:
  # Standard config
  - /var/run/docker.sock:/var/run/docker.sock
  - /source:/app/source
  - /destination:/app/destination
  # Alternative source directories examples
  - /opt/pihole:/app/source/pihole
  - /mnt/docker_volumes/plex:/app/source/plex
```

This config allows the addition of volumes outside the traditional `source` directory.

We added 2 additional source volumes: `pihole` and `plex`. The end result will have a source directory inside the Nautical container that looks like this:

```bash
<Nautical Backup>/app/source:
 - container1-data #(1)!
 - container2-data #(2)!
 - pihole           # Mapped from /opt/pihole
 - plex             # Mapped from /mnt/docker_volumes/plex
```

1. This is an example container data folder from the mounted `/source` directory
2. This is an example container data folder from the mounted `/source` directory

### Alternative Only
```yaml
volumes:
  # Standard config
  - /var/run/docker.sock:/var/run/docker.sock
  - /destination:/app/destination
  # Alternative source directories examples
  - /opt/pihole:/app/source/pihole
  - /opt/trilium:/app/source/trilium
  - /mnt/docker_volumes/plex:/app/source/plex
  - /var/data/portainer:/app/source/portainer
```
This configuration allows us to map as many container data folders as we'd like from any source directory.
```yaml
<Nautical Backup>/app/source:
 - pihole     # Mapped from /opt/pihole
 - trilium    # Mapped from /opt/trilium
 - plex       # Mapped from /mnt/docker_volumes/plex
 - portainer  # Mapped from /var/data/portainer
```

## Alternative Destination Directories
We can also remap the distination directory for any container we'd like.

!!! tip "Remember the folder naming convention"
    1. The `container-name` must match the `source` and `destination` folder names.
    2. You can override this using [Aruguments](../arguments.md#override-destination-directory).

### Sandard and Alternative
```yaml
volumes:
  # Standard config
  - /var/run/docker.sock:/var/run/docker.sock
  - /source:/app/source
  - /destination:/app/destination
  # Alternative destination directories examples
  - /opt/pihole-backup:/app/destination/pihole
  - /mnt/docker_volume-backups/plex:/app/destination/plex
```

This config allows the addition of volumes outside the traditional `destination` directory.

We added 2 additional destination volumes: `pihole` and `plex`. The end result will have a destination directory inside the Nautical container that looks like this:

```yaml
<Nautical Backup>/app/destination:
 - container1-data #(1)!
 - container2-data #(2)!
 - pihole           # Mapped to /opt/pihole-backup
 - plex             # Mapped to /mnt/docker_volume-backups/plex
```

1. This is an example container data folder from the mounted `/source` directory
2. This is an example container data folder from the mounted `/source` directory

### Alternative Only
```yaml
volumes:
  # Standard config
  - /var/run/docker.sock:/var/run/docker.sock
  - /source:/app/source
  # Alternative destination directories examples
  - /opt/pihole:/app/destination/pihole
  - /opt/trilium:/app/destination/trilium
  - /mnt/docker_volumes/plex:/app/destination/plex
  - /var/data/portainer:/app/destination/portainer
```
This configuration allows us to map as many container data folders as we'd like to any destination directory.
```yaml
<Nautical Backup>/app/destination:
 - pihole     # Mapped to /opt/pihole
 - trilium    # Mapped to /opt/trilium
 - plex       # Mapped to /mnt/docker_volumes/plex
 - portainer  # Mapped to /var/data/portainer
```