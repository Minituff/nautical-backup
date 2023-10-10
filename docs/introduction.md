Nautical Backup is designed to be a simple and easy way to use tool to backup your docker volumes.

Essentially, this is an automated and confugurable backup tool built around [rsync](https://en.wikipedia.org/wiki/Rsync). 
## Backups Made Easy

Nautical requires almost no configuration when container volumes are all in a folder matching its `container-name` within the source directory. Of course, we can use [variables](./arguments.md) to override these defaults.

⚓ Here is an example of an *easy-mode* configuration:

| Container Name | *Example* Source Data Directory     | *Example* Desitnation Data Directory   |
| -------------- | ----------------------------------- | -------------------------------------- |
| homeassistant  | `/opt/docker-volumes/homeassistant` | `/mnt/nfs-share/backups/homeassistant` |
| unifi          | `/opt/docker-volumes/unifi`         | `/mnt/nfs-share/backups/unifi`         |
| plex           | `/opt/docker-volumes/plex`          | `/mnt/nfs-share/backups/plex`          |
| homepage       | `/opt/docker-volumes/homepage`      | `/mnt/nfs-share/backups/homepage`      |
| traefik        | `/opt/docker-volumes/traefik`       | `/mnt/nfs-share/backups/traefik`       |
| portainer      | `/opt/docker-volumes/portainer`     | `/mnt/nfs-share/backups/portainer`     |
| trilium        | `/opt/docker-volumes/trilium`       | `/mnt/nfs-share/backups/trilium`       |
| dozzle         | *No data directory*                 | *No backup*                            |

## Logical Workflow
Once the CRON job triggers the script to run, the following steps will be executed in order:

1. All running contianers will be listed by `name` and `id`
2. The `source` and `destination` paths will be overritten if necessary.
    *  This is done using [overrides](./arguments.md#override-source-directory)
3. The `source` and `destination` will be verified
    * *read* permissions for the source
    * *read & write* permissions for the destination
4. The container will be *skipped* if:
    * The container fails the previous step
    * The container does not have a matching `source` folder <small>(if not using [overrides](./arguments.md#override-source-directory))</small>
    * The container is in the [skip](./arguments.md#skip-containers) list
5. The container will be stoped ❌
6. The `source` folder will be copied to the `destination`
    * Except for excluded files
7. The container will be started again ✔️
8. A `Backup Report (today's date).txt` will be created in `destination`
      * This report can be disabled using [variables](./arguments.md#report-file)


!!! warning "The container needs a matching `directory` name inside the `source` folder."
    !!! abstract "Only if you are not using [overrides](./arguments.md#override-source-directory)."
    For example:

    * A container named `portainer` will be backed up with the mounted directory `/source/portainer`
    
    * A container named `trilium` will be backed up with the mounted directory `/source/trilium`

    * A container named `portainer` will be ==skipped== with the mounted directory `/source/portainer-data`

    A container with *no* directory will just be skipped. For example:

    * A container named `dozzle` has no mounted directory, so it wil be skipped.


## Selection Example
 This example can help explain how Nautical decides which containers to backup.

 Assume the `src` directory is folder mounted in the container: `-v /src:/app/source`

| Conatianer Name | Data Directory       | Action | Reasoning                                 |
| --------------- | -------------------- | ------ | ----------------------------------------- |
| homeassistant   | `/src/homeassistant` | Backup |                                           |
| unifi           | `/src/unifi`         | Backup |                                           |
| tautulli        | `/src/plex-data`     | Skip   | Container name and data dir don't match   |
| homepage        | `/src/home-continer` | Skip   | Container name and data dir don't match   |
| dozzle          | *No data directory*  | Skip   | No data directory matching container name |
| watchtower      | *No data directory*  | Skip   | No data directory matching container name |
| traefik         | `/src/traefik/data`  | Backup | `traefik` and all subfolders              |
| portainer       | `/src/portainer`     | Backup |                                           |
| trilium         | `/src/trilium`       | Backup |                                           |

!!! note "`homepage` and `tautulli` can still be backed up."
    You just need to use [Source Location Overrides](./arguments.md#override-source-directory)