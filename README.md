<div align="center">
    <img width="400" alt="Logo" src="./docs/media/Logo-transparent.png"/>
    
A simple Docker volume backup tool.

---

<br>

  [![Pulls from DockerHub](https://img.shields.io/docker/pulls/minituff/nautical-backup?logo=docker)](https://hub.docker.com/r/minituff/nautical-backup)

</div>

### Documentation
Full documentation is available at [https://minituff.github.io/nautical-backup](https://minituff.github.io/nautical-backup)

### Quick Start

```yaml
---
version: '3'
services:
  nautical-backup:
    image: minituff/nautical-backup:0.0.4
    container_name: nautical-backup
    hostname: nautical-backup
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /source:/app/source
      - /destination:/app/destination
    environment:
      # Optional variables
      - TZ=America/Los_Angeles
      - CRON_SCHEDULE=0 4 * * *
      - SKIP_CONTAINERS=example1,example2,example3
```

```bash
docker run -d \
  --name nautical-backup \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /source:/app/source \
  -v /destination:/app/destination \
  -e CRON_SCHEDULE="0 4 * * *" \
  -e SKIP_CONTAINERS="example1,example2,example3" \
  minituff/nautical-backup:0.0.4
```