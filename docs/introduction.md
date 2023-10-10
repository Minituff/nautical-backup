Nautical Backup is designed to be a simple and easy way to use tool to backup your docker volumes.

### How it works
Once the CRON job triggers the script to run:

1. All running contianers will be listed by `name` and `id`
1. `source_location` and `destination_location` will be verified
    * *read* permissions for the source
    * *read + write* permissions for the destination
1. The container will be *skipped* if:
    * The `container_name` does not match `source_location`
    * The `container_name` has *no* matching `source_location`
    * The `container_name` is in the `default_skips` list
1. The container will be stoped ❌
1. The `source_location` and `destination_location` will be overritten if necessary.
1. The entire `source_location` folder will be copied to the `destination_location`
1. The container will be started again ✔️
1. A `Backup Report (today's date).txt` will be created in `destination_location`
      * This report can be disabled


!!! warning "The `container_name` needs the same `directory` name inside the `source_location` folder."
    For example:

    * The container named `portainer` will be backed up with the mounted directory `/source/portainer`
    
    * The container named `trilium` will be backed up with the mounted directory `/source/trilium`

    * The container named `trilium` will be ==skipped== with the mounted directory `/source/trilium-data`

    A container with *no* directory will just be skipped. For example:

    * The container named `dozzle` has no mounted directory, so it wil be skipped.

<br>

## Example
 This example can help explain how Nautical decides which containers to backup.

 Assume the `src` directory is folder mounted in the container: `-v /src:/app/source`

| Conatianer Name | Data Directory       | Action | Reasoning                                 |
| --------------- | -------------------- | ------ | ----------------------------------------- |
| homeassistant   | `/src/homeassistant` | Backup |                                           |
| unifi           | `/src/unifi`         | Backup |                                           |
| tautulli        | `/src/plex-data`     | Skip   | Container name and data dir don't match   |
| homepage        | `/src/dashboard`     | Skip   | Container name and data dir don't match   |
| dozzle          | *No data directory*  | Skip   | No data directory matching container name |
| watchtower      | *No data directory*  | Skip   | No data directory matching container name |
| traefik         | `/src/traefik/data`  | Backup | `traefik` and all subfolders              |
| portainer       | `/src/portainer`     | Backup |                                           |
| trilium         | `/src/trilium`       | Backup |                                           |