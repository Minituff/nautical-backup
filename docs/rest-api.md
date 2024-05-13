## Enable The API
The API is ^^enabled internally by default^^, but you still must open the port for external access. Follow these steps:

!!! abstract "Why is the REST API on internally?"
    The REST API is used internally for Docker [Healthchecks](https://docs.docker.com/reference/dockerfile). 
    However, if do not open the port via Docker, then all the endpoints will remain unreachable.

### 1. Map the port
You need to ensure the port is opened by Docker for the Nautical container. See the ==highlighted== sections of this example Nautical config:

=== "Docker Compose"
    ```yaml hl_lines="11 12 13"
    ------8<------ "docker-compose-example-no-tooltips.yml:0:11"
        ports:
          - "8069:8069/tcp"
    ```
    
=== "Docker Cli"

    ```bash hl_lines="6 6"
    ------8<------ "docker-run-example-no-tooltips.sh::6"
      -p 8069:8069/tcp \
    ------8<------ "docker-run-example-no-tooltips.sh:10:"
    ```

### 2. Verify it works
To view the API, go to http://localhost:8069/docs in your browser.

## Authentication

The default login is `admin` / `password`.
This can be changed [here](./arguments.md/#api-username-and-password).

```bash
curl -X GET \
  'http://localhost:8069/auth' \
  --header 'Authorization: Basic YWRtaW46cGFzc3dvcmQ='
```

!!! tip "Use [this](https://mixedanalytics.com/tools/basic-authentication-generator) site to generate a Base64 token."

## Dashboard
> GET
> /api/v1/nautical/dashboard

This endpoint is the quickest way to get a glimpse into everything Nautical has going on.

???+ example "Example response"
    ```json
    {
      "next_cron": {
        "1": [
          "Monday, November 20, 2023 at 04:00 AM",
          "11/20/23 04:00"
        ],
        "2": [
          "Tuesday, November 21, 2023 at 04:00 AM",
          "11/21/23 04:00"
        ],
        "3": [
          "Wednesday, November 22, 2023 at 04:00 AM",
          "11/22/23 04:00"
        ],
        "4": [
          "Thursday, November 23, 2023 at 04:00 AM",
          "11/23/23 04:00"
        ],
        "5": [
          "Friday, November 24, 2023 at 04:00 AM",
          "11/24/23 04:00"
        ],
        "cron": "0 4 * * *",
        "tz": "America/Los_Angeles"
      },
      "next_run": "11/20/23 04:00",
      "last_cron": "11/19/23 04:00",
      "number_of_containers": "1",
      "completed": "0",
      "skipped": "1",
      "errors": "0",
      "backup_running": "false"
    }
    ```

## Next CRON

> GET
> /api/v1/nautical/next_cron/{occurrences}
> 
> {occurrences} = integer between 1 and 100

Get the next *n* scheduled times Nautical will run.

???+ example "Example response"
    ```json
    {
      "1": [
        "Monday, November 20, 2023 at 04:00 AM",
        "11/20/23 04:00"
      ],
      "2": [
        "Tuesday, November 21, 2023 at 04:00 AM",
        "11/21/23 04:00"
      ],
      "cron": "0 4 * * *",
      "tz": "America/Los_Angeles"
    }
    ```

## Start Backup

> POST
> /api/v1/nautical/start_backup

Start a backup now. The API will not respond until the backup has completed. 

All the [Variables](./arguments.md) and [Labels](./labels.md) are respected.

???+ example "Example response"
    ```json
    {
      "message": "Nautical Backup completed successfully"
    }
    ```

## Kickoff Backup

> POST
> /api/v1/nautical/kickoff_backup

Start a backup now in the background. The API will respond immediately.

All the [Variables](./arguments.md) and [Labels](./labels.md) are respected.

???+ example "Example response"
    ```json
    {
      "message": "Nautical Backup started successfully"
    }
    ```
