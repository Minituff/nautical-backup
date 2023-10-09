
## Docker Compose Example

```yaml
---
version: '3'
services:
  nautical-backup:
    image: minituff/nautical-backup:0.0.3 #(7)!
    container_name: nautical-backup
    hostname: nautical-backup
    restart: unless-stopped
    volumes:
    - /var/run/docker.sock:/var/run/docker.sock #(1)!
    - /source:/app/source #(2)!
    - /destination:/app/destination #(3)!
    environment:
      # Optional variables (4)
      - TZ=America/Los_Angeles
      - CRON_SCHEDULE=* 4 * * * #(5)!
      - SKIP_CONTAINERS=example1,example2,example3 #(6)!
```

1. Mount the docker socket. Used to start and stop containers.
2. Mount the `source` directory.
3. Mount the `destination` directory.
4. *TIP*: Avoid using "quotes" in the enviornment variables.
5. Scheduled time to run backups. Use [this website](https://crontab.guru) to help pick a CRON schedule.
    * Default = `0 4 * * *` - Every day at 4am.
6. Containers to skip. A comma seperated list.
7. It is recommended to avoid using the `latest` tag.
    * This project is under active development, using a exact tag can help avoid updates breaking things.


## Docker Run Example

```bash
docker run -d \
--name nautical-backup:0.0.3 \ #(7)!
-v /var/run/docker.sock:/var/run/docker.sock \ #(1)!
-v /source:/app/source \ #(2)!
-v /destination:/app/destination \ #(3)!
-e CRON_SCHEDULE="* 4 * * *" \ #(5)!
-e SKIP_CONTAINERS="example1,example2,example3" \ #(6)!
minituff/nautical-backup
```

1. Mount the docker socket. Used to start and stop containers.
2. Mount the `source` directory.
3. Mount the `destination` directory.
4. *TIP*: Avoid using "quotes" in the enviornment variables.
5. Scheduled time to run backups. Use [this website](https://crontab.guru) to help pick a CRON schedule.
    * Default = `0 4 * * *` - Every day at 4am.
6. Containers to skip. A comma seperated list.
7. It is recommended to avoid using the `latest` tag.
    * This project is under active development, using a exact tag can help avoid updates breaking things.

<br>
