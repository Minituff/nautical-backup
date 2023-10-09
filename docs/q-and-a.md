

####  Why do we need docker volume backups?
If your Docker Host machine doesn't take snapshots like a ZFS TrueNAS machine does. This means that even though we may have redundancy, it doesn't protect aginst fauly configuration or complete deletion of our container data.

#### Why don't I store the container volumes directly on a NFS share?
This is common idea, but SQL databases would constantly go into a locked state about once every few weeks.
This method has been much more reliable.

#### Why do we need to stop the container before a backup?
This is important for containers that run databases, especially SQL. During database access, the database will be temporarily locked during a write action and then unlocked afterwards. If a container is backed up during a databse lock, then your backup could become corrupted.

Stopping the container guarantees it was given the proper time to gracefully stop all services before we create a backup. Yes, there will be downtime for this, but it is only a few seconds and you can schedule this to run in off-peak hours.

#### Why don't we backup the container itself?
Containers are meant to be ephemeral, and essentially meaniningless. The goal is to have only the data referenced by the container be important--not the container itself.

If something bad happened to our entier docker stack, we only need the `docker-compose` files and the data they referenced. This would allow us to be back online in no time!

If you would like to save data or changes within the docker container, consider making a new image. This would save the modification steps and allow it to be easily replicated.
