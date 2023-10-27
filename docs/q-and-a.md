###  Why do we need docker volume backups?
If your Docker Host machine doesn't take snapshots like a ZFS-based machine does, then you aren't protected against faulty configuration or complete deletion of our container data.

### Why do we need to stop the container before a backup?
This is important for containers that run databases, especially SQL. During database access, the database will be temporarily locked during a write action and then unlocked afterwards. If a container is backed up during a datable lock, then your database could become corrupted.


Stopping the container guarantees it was given the proper time to gracefully stop all services and unlock the databases before we create a backup. Yes, there will be downtime for this, but it is only a few seconds and you can schedule this to run in off-peak hours.

### Why don't I store the container volumes directly on a NFS share?
This is common idea, but SQL databases would constantly go into a locked state about once every few weeks. <small>(This happens frequently with apps like [Sonarr](https://github.com/Sonarr/Sonarr), [Radarr](https://github.com/radarr/radarr), [Prowlarr](https://github.com/Prowlarr/Prowlarr), etc.)</small>
Stopping the container first is the only way to guarantee there is no corruption.

### Why don't we backup the entire container itself?
Containers are meant to be ephemeral, and essentially meaningless. The goal is to have only the data referenced by the container be important----not the container itself.

If something bad happened to the docker stack, we only need the `docker-compose` files and the data they referenced. This would allow us to be back online in no time!

If you would like to save data or changes within the docker container, consider making a new image. This would save the modification steps and allow it to be easily replicated.

### Does Nautical support remote backups?
This question is answered [here](./advanced/remote-backups.md).

### Where do I run Nautical?
Nautical is only able to access the Docker containers running *on the same machine as the Nautical container itself*. So if you run multiple VMs/LXCs that have unique Docker installations on each of them, then you would need to install Nautical on each one.