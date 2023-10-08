<div align="center">
    <img width="400" alt="Title" src="./media/Logo-transparent.png"/>
    
    # Nautical backup
    A simple container to backup your container volumes.
    <br/><br/>
</div>

### How it works
Once the CRON job triggers the script to run:

1. All running contianers will be listed by `name`
1. `source_location` and `destination_location` will be verified
1. The container will be *skipped* if:
    * The `container_name` does not match `source_location`
    * The `container_name` has *no* matching `source_location`
    * The `container_name` is in the `default_skips` list
1. The container will be stoped ❌
1. The entire `source_location` folder will be copied to the `destination_location`
1. The container will be started again ✔️
1. A `Backup Report (today's date).txt` will be created in `destination_location`

> [!WARNING] This script requires the `container_name` to be the same as the `directory` name inside the `source_location` folder.
>    For example: 
>    
>    * The container named `portainer` has the mounted directory `/opt/docker_volumes/portainer`
>    
>    * The container named `trilium` has the mounted directory `/opt/docker_volumes/trilium`
>
>    A container with *no* directory will just be skipped. For example:
>
>    * The container named `dozzle` has no mounted directory, so it wil be skipped


### Docker Compose Example
```yaml
---
version: '3.3'
services:
  nautical-backup:
    image: minituff/nautical-backup:latest
    container_name: nautical-backup
    hostname: nautical-backup
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /source-path:/app/source # Mount source directory
      - /destination-path:/app/destination # Create destination directory
    environment:
      - CRON_SCHEDULE=0 4 * * *
    restart: unless-stopped

```
### ❓Questions

####  Why do we need docker volume backups?
If your Docker Host machine doesn't take snapshots like a ZFS TrueNAS machine does. This means that even though we may have redundancy, it doesn't protect aginst fauly configuration or complete deletion of our container data.

#### Why don't I store the container volumes directly on a NFS share?
This is common idea, but SQL databases would constantly go into a locked state about once every few weeks.
This method has been much more reliable.

#### Why do we need to stop the container before a backup?
This is important for containers that run databases, especially SQL. During database access, the database will be temporarily locked during a write action and then unlocked afterwards. If a container is backed up during a databse lock, then your backup could become corrupted.

Stopping the container guarantees it was given the proper time to gracefully stop all services before we create a backup. Yes, there will be downtime for this, but it is only a few seconds and you can schedule this to run in off-peak hours.

####  Why don't we backup the container itself?
Containers are meant to be ephemeral, and essentially meaniningless. The goal is to have only the data referenced by the container be important--not the container itself.

If something bad happened to our entier docker stack, we only need the `docker-compose` files and the data they referenced. This would allow us to be back online in no time!

If you would like to save data or changes within the docker container, consider making a new image. This would save the modification steps and allow it to be easily replicated.

## Useful commands

```bash
docker run -e CRON_SCHEDULE="* * * * *" -d nautical-backup
```

```bash
docker run --detach --name watchtower --volume /var/run/docker.sock:/var/run/docker.sock containrrr/watchtower
```