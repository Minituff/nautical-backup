1. Run the test container

```bash
cd tests
docker compose run nautical-backup-test4
```
!!! tip "You may need to update the paths here to be absolute paths"
    This is a problem with DevContainers

1. Shell into the container

```bash
docker exec -it nautical-backup-test
```

1. Run the tests

```bash
with-contenv bash _tests.sh 
```
!!! tip "`with-contenv` preserves environment variables"