docker run -d \
  --name nautical-backup \
  -v /var/run/docker.sock:/var/run/docker.sock \ #(1)!
  -v /source:/app/source \ #(2)!
  -v /destination:/app/destination \ #(3)!
  -e CRON_SCHEDULE="0 4 * * *" \ #(5)!
  -e SKIP_CONTAINERS="example1,example2,example3" \ #(6)!
  minituff/nautical-backup:0.0.6 #(7)!