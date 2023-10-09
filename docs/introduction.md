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

!!! warning "The `container_name` needs the same `directory` name inside the `source_location` folder."
    For example: 
    
    * The container named `portainer` has the mounted directory `/source/portainer`
    
    * The container named `trilium` has the mounted directory `/source/trilium`

    * The container named `trilium` will *not* workd with the mounted directory `/source/trilium-data`

    A container with *no* directory will just be skipped. For example:

    * The container named `dozzle` has no mounted directory, so it wil be skipped.


<br>