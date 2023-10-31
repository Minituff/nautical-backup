
Essentially, this is an automated and configurable backup tool built around [rsync](https://en.wikipedia.org/wiki/Rsync). 

## The Basics
Nautical runs `Bash` commands on a `CRON` schedule to:

1. Stop the container <small>(if configured)</small>
2. Run the backup via `rsync`
3. Restart the container <small>(if stopped)</small>

⚗️ **Need more control?** There are many more options available via [variables](./arguments.md) and [labels](./labels.md).



##  Sample Configuration
Nautical requires almost no configuration when container volumes are all in a folder matching its `container-name` within the source directory.  <small>Of course, we can use [variables](./arguments.md) and [labels](./labels.md) to override these defaults. </small>

Let's take a look at an example:

| Container Name                                      | Source Data Directory                 | Destination Data Directory                    |
| --------------------------------------------------- | ------------------------------------- | --------------------------------------------- |
| [homepage](https://github.com/gethomepage/homepage) | `/opt/docker-volumes/homepage`        | `/mnt/nfs-share/backups/homepage`             |
| [trilium](https://github.com/zadam/trilium)         | `/opt/docker-volumes/trilium`         | `/mnt/nfs-share/backups/trilium`              |
| [dozzle](https://github.com/amir20/dozzle)          | *N/A* <small>(no data folder)</small> | *N/A*       <small>(no backup needed)</small> |

!!! example "Here is how Nautical fits into the *Sample Configuration*"
    === "Docker Compose"
        ```yaml
        ------8<------ "docker-compose-example.yml:3:8"
              - /opt/docker-volumes:/app/source #(2)!
              - /mnt/nfs-share/backups:/app/destination #(3)!
        ```
        
        ------8<------ "docker-example-tooltips.md"

    === "Docker Cli"
        ```bash
        ------8<------ "docker-run-example.sh::4"
          -v /opt/docker-volumes:/app/source \ #(2)!
          -v /mnt/nfs-share/backups:/app/destination \ #(3)!
        ------8<------ "docker-run-example.sh:10:"
        ```

        ------8<------ "docker-example-tooltips.md"
