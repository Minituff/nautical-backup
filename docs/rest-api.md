<!-- https://blueswen.github.io/mkdocs-swagger-ui-tag/ -->

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

???+ example "Example response"
    ```json
    ```