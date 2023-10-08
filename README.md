
# Nautical backup
TODO: Add this later

## Useful commands

```bash
docker run -e CRON_SCHEDULE="* * * * *" -d nautical-backup
```

```bash
docker run --detach --name watchtower --volume /var/run/docker.sock:/var/run/docker.sock containrrr/watchtower
```