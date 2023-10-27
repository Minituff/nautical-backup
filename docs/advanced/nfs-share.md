Nautical itself does not have the ability to map network shares. However, it can use a network share for either the source or destination.

Commonly, we run containers on our host machine, then use an NFS share as the backup destination location. This page will give a brief overview of how to do that.

## Connect to an NFS Share On Container Host (Linux)

1. Create the NFS destination directories.
    ```bash
    # Create mount point (1)
    mkdir -p /mnt/nfs/docker_backups
    ```
   
    1. The destination directories must exist before a mount can be created  


2. Setup NFS mount points: 
    ```bash
    nano /etc/fstab
    ```
    This will open a file, and here you can insert your NFS configuration:
    ```bash title="/etc/fstab"
    # | ------------- Source -------------- | ---- Destination ---- | -------- Options ---------- |
    192.168.1.10:/mnt/backups/docker_volumes /mnt/nfs/docker_backups nfs _netdev,auto,rw,async 0 0
    ```
    <small>**Tip:** `192.168.1.10` is just an example IP address</small>

3. Apply and mount the NFS shares
    ```bash 
    mount -a
    ```

    !!! success "A successful `mount -a` will return *nothing* in the console"

4. Verify *read* and *write* access
    ```bash
    cd /mnt/nfs/docker_backups
    touch test.txt && rm test.txt
    ```

## Add Nautical Backup

The above example created a local directory of `/mnt/nfs/docker_backups` which is an NFS share pointing to `192.168.1.10:/mnt/backups/docker_volumes`.

Here is how we can use this new mount withing Nautical:
=== "Docker Compose"
    ```yaml  hl_lines="9"
    ------8<------ "docker-compose-example.yml:0:9"
          - /mnt/nfs/docker_backups:/app/destination #(3) <-- NFS Share

    ```

    ------8<------ "docker-example-tooltips.md"

=== "Docker Run"
    ```bash hl_lines="5"
    ------8<------ "docker-run-example.sh:0:5"
      -v /mnt/nfs/docker_backups:/app/destination \ #(2)!
    ------8<------ "docker-run-example.sh:10:"
    ```

    ------8<------ "docker-example-tooltips.md"