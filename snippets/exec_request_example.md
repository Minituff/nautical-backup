!!! example "Test your `exec`"
    Before setting the variable/label, it is a good idea to ensure it works first. Here is an example.

    Ensure Nautical is running first, then run:
    ```bash
    docker exec -it nautical-backup \
      curl -X GET 'google.com'
    ```
    **Note:** You can only have 1 *before* and 1 *after* Curl Request. This applies to Nautical itself, not to each container.


??? abstract "Running a script"
    If you need to run more than a simple one-liner, we can run an entire script instead.
    Here is a basic example:

    Create a file <small>(we will name it `script.sh`)</small> and place it in the mounted `/config` directory.

    **Remeber:** We set the `/config` folder as part of the [Installation](./installation.md).
    
    ```bash
    #!/usr/bin/env bash

    echo "Hello from script.sh"

    echo "NB_EXEC_COMMAND: $NB_EXEC_COMMAND" 
    echo "NB_EXEC_ATTACHED_TO_CONTAINER: $NB_EXEC_ATTACHED_TO_CONTAINER" 
    echo "NB_EXEC_CONTAINER_NAME: $NB_EXEC_CONTAINER_NAME" 
    echo "NB_EXEC_CONTAINER_ID: $NB_EXEC_CONTAINER_ID" 
    echo "NB_EXEC_BEFORE_DURING_OR_AFTER: $NB_EXEC_BEFORE_DURING_OR_AFTER" 

    ```