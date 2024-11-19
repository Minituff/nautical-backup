
docker run -d \
  --name nautical-backup \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /config:/config \
  -v /source:/app/source \
  -v /destination:/app/destination \
  -e TZ="America/Los_Angeles" \
  -e CRON_SCHEDULE="0 4 * * *" \
  -e SKIP_CONTAINERS="example1,example2,example3" \
  minituff/nautical-backup:2.8