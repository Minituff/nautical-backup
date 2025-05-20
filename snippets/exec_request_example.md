??? example "Test your `exec`"
    Before setting the variable/label, it is a good idea to ensure it works first. Here is an example.

    Ensure Nautical is running first, then run:
    ```bash
    docker exec -it nautical-backup \
      curl -X GET 'google.com'
    ```
    **Note:** You can only have 1 *before* and 1 *after* Curl Request. This applies to Nautical itself, not to each container.

??? quote "Available Enviornment Variables"

    | Method                               | Description                                                                             |
    |:-------------------------------------|:----------------------------------------------------------------------------------------|
    | `NB_EXEC_CONTAINER_NAME`             | The container name*                                                                     |
    | `NB_EXEC_CONTAINER_ID`               | The contianer ID*                                                                       |
    | `NB_EXEC_BEFORE_DURING_OR_AFTER`     | When is this command being. [Options](./arguments.md#when-to-backup-additional-folders) |
    | `NB_EXEC_COMMAND`                    | The exact command exectuted                                                             |
    | `NB_EXEC_ATTACHED_TO_CONTAINER`      | Is this exec command attached to a container                                            |
    |                                      |                                                                                         |
    | `NB_EXEC_TOTAL_ERRORS`               | The total errors on the last run+                                                       |
    | `NB_EXEC_TOTAL_CONTAINERS_COMPLETED` | The amount of containers processed successfully+                                        |
    | `NB_EXEC_TOTAL_CONTAINERS_SKIPPED`   | The amount of containers skipped (for any reason)+                                      |
    | `NB_EXEC_TOTAL_NUMBER_OF_CONTAINERS` | The amount of containers Nautical looked at+                                            |

    <small> * Require access to a container. Eg. When `NB_EXEC_ATTACHED_TO_CONTAINER=true`</small> 

    <small> + Must be used `AFTER` so there are values to fill. Eg. When `nautical-backup.exec.after`</small> 

    💰 **Tip:** To use the enviornment variables in a docker-compose file, you will need to escape them with a double `$`:
    ```yaml
    labels:
      - "nautical-backup.exec.before=echo name: $$NB_EXEC_CONTAINER_NAME" # (1)!
    ```

    1. Notice the double `$$`

    🛎️ Want any additional enviornment variables? Submit an [issue](https://github.com/Minituff/nautical-backup/issues/new).


??? abstract "Executing a script"
    If you need to run more than a simple one-liner, we can run an entire script instead.
    Here is a basic example:

    Create a file <small>(we will name it `script.sh`)</small> and place it in the mounted `/config` directory.

      **Remember:** We mounted the `/config` folder as part of the [Installation](./installation.md).
    
    ```bash
    #!/usr/bin/env bash

    echo "Hello from script.sh"

    # Variable usage example
    echo "NB_EXEC_CONTAINER_NAME: $NB_EXEC_CONTAINER_NAME" 
    echo "NB_EXEC_CONTAINER_ID: $NB_EXEC_CONTAINER_ID" 
    ```

    Give the file execution permission: `chmod +x /config/script.sh`

    **Test the script**

    Ensure Nautical is running first, then run:
    ```bash
    docker exec -it nautical-backup \
      /bin/bash /config/script.sh
    ```

