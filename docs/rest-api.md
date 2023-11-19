<!-- https://blueswen.github.io/mkdocs-swagger-ui-tag/ -->


## Enable The API
The API is ^^disabled by default^^; turning it on is simple. Follow these 3 steps:

### 1. Set the environment variable

See the [variables section](./arguments.md#http-rest-api) for more information.

```properties
HTTP_REST_API_ENABLED=true
```

Once enabled, you will see the following message after starting the Nautical container logs.
> INFO: API listening on port 8069...

### 2. Map the port
Next, you need to ensure you map the port from the Nautical container.
Add the ==highlighted== section to your Nautical config.

=== "Docker Compose"
    ```yaml hl_lines="10 11"
    ------8<------ "docker-compose-example-no-tooltips.yml:0:10"
        ports:
          - "8069:8069/tcp"
    ```
    
=== "Docker Cli"

    ```bash hl_lines="6"
    ------8<------ "docker-run-example-no-tooltips.sh::6"
      -p 8069:8069/tcp
    ------8<------ "docker-run-example-no-tooltips.sh:10:"
    ```

### 3. Verify it works
To view the API, go to http://localhost:8069/docs in your browser.

## Authentication

The default login is `admin` / `password`.
This can be changed [here](./arguments.md/#api-username-and-password).

```bash
curl -X GET \
  'http://localhost:8069/auth' \
  --header 'Authorization: Basic YWRtaW46cGFzc3dvcmQ='
```

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
      "last_cron": [
        "Sunday, November 19, 2023 at 11:24 AM",
        "11/19/23 11:24"
      ],
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

Start a backup now. All the [Variables](./arguments.md) and [Labels](./labels.md) are respected.

???+ example "Example response"
    ```json
    {
      "message": "Nautical Backup started successfully"
    }
    ```