1. Mount the docker socket. Used to start and stop containers.
2. Mount the `source` directory.
3. Mount the `destination` directory.
4. *TIP*: Avoid using "quotes" in the enviornment variables.
5. Scheduled time to run backups. Use [this website](https://crontab.guru) to help pick a CRON schedule.
    * Default = `0 4 * * *` - Every day at 4am.
6. Containers to skip. A comma seperated list.
7. It is recommended to avoid using the `latest` tag.
    * This project is under active development, using a exact tag can help avoid updates breaking things.