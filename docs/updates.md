Updating Nautical <small>(and any continer)</small> is a balance between *convenience*, *reliability* and *security*.

Updating your container will bring new features, bug fixes and security patches but can also introduce intended behavior.


## Understanding Semantic Versioning
[Semver](https://semver.org) is a means to communicate the changes to an application just by looking at the version number.
Nautical uses [Semver](https://semver.org) like this.

`vMAJOR.MINOR.PATCH`, for example:
<a href="https://hub.docker.com/r/minituff/nautical-backup"><img alt="Docker Image Version (latest semver)" src="https://img.shields.io/docker/v/minituff/nautical-backup/latest?label= " /></a>

* **MAJOR** - A large change that breaks/reworks an existing feature. 
    * This usually means you will need to change the Nautical configuration.
* **MINOR** - Add functionality in a backward compatible manner.
    * Everything *should* continue working without changes to the Nautical configuration.
* **PATCH** - A small change such as updating a depedency, log output, or minor fix.
    * From the user perspective, nothing will have changed, but under the hood, small improvements were made.

## Manual Updates
To manually update Nautical, simply re-deploy using either of these configs, but specify the latest version of the Nautical.
Currently, the latest version of Nautical is <a href="https://hub.docker.com/r/minituff/nautical-backup"><img alt="Docker Image Version (latest semver)" src="https://img.shields.io/docker/v/minituff/nautical-backup/latest?label= " /></a>. <small>(do not add the `v`)</small>

This will need to be done each time a new verison is released.
=== "Docker Compose"
    ```yaml
    ------8<------ "docker-compose-semver-example.yml:3"
    ------8<------ "docker-compose-example.yml:6:10"
    ```
    
    ------8<------ "docker-example-tooltips.md"

=== "Docker Cli"

    ```bash
    ------8<------ "docker-run-example.sh::6"
    ------8<------ "docker-run-semver-example.sh"

      # Update the version number in the line above
    ```

    ------8<------ "docker-example-tooltips.md"


## Automatic Updates
[Watchtower](https://github.com/containrrr/watchtower/) is an excellent tool to keep your Docker containers update.

While convenient, automatic updates may break things. For this reason we recommend only automatically updating to the latest `PATCH` version.

=== "Patch Updates Only"
    !!! note ""
        These examples only specify the [Semver](https://semver.org) `vMAJOR.MINOR` numbers, leaving `PATCH` out--this means that Watchtower will update the `PATCH` number if available.

        === "Docker Compose"
            ```yaml hl_lines="3"
            ------8<------ "docker-compose-example.yml:3:10"
              
              watchtower:
                image: containrrr/watchtower:latest
                container_name: watchtower
                volumes:
                  - /var/run/docker.sock:/var/run/docker.sock
                command: nautical-backup # (9)! 
            ```

            ------8<------ "docker-example-tooltips.md"
            1. Which containers to use. 

                Remove this line to update all contianers.

        === "Docker Cli"
            ```bash hl_lines="6"
            ------8<------ "docker-run-example.sh::6"
            ------8<------ "docker-run-example.sh:10:"
            
            docker run -d \
              --name watchtower \
              -v /var/run/docker.sock:/var/run/docker.sock \
              containrrr/watchtower \
              nautical-backup #(9)!
            ```

            ------8<------ "docker-example-tooltips.md"
            1. Which containers to use. 

                Remove this line to update all contianers.

=== "Minor And Patch Updates"
    !!! note ""
        These examples specify the [Semver](https://semver.org) `vMAJOR` number, leaving `MINOR` `PATCH` out--this means that Watchtower will update `MINOR` and `PATCH` versions if available.

        === "Docker Compose"
            ```yaml hl_lines="3"
            ------8<------ "docker-compose-semver-major-example.yml:3:10"
              
              watchtower:
                image: containrrr/watchtower:latest
                container_name: watchtower
                volumes:
                  - /var/run/docker.sock:/var/run/docker.sock
                command: nautical-backup # (9)! 
            ```

            ------8<------ "docker-example-tooltips.md"
            1. Which containers to use. 

                Remove this line to update all contianers.

        === "Docker Cli"
            ```bash  hl_lines="6"
            ------8<------ "docker-run-example.sh::6"
            ------8<------ "docker-run-semver-major-example.sh"
            
            docker run -d \
              --name watchtower \
              -v /var/run/docker.sock:/var/run/docker.sock \
              containrrr/watchtower \
              nautical-backup #(9)!
            ```

            ------8<------ "docker-example-tooltips.md"
            2. Which containers to use. 

                Remove this line to update all contianers.

=== "Latest Updates (All)"
    !!! note ""
        If you're really feeling like living on the bleeding edge. You can use the `latest` tag to ensure you are always up to date.
        This will get the latest [Semver](https://semver.org) `MAJOR`, `MINOR`, and `PATCH` updates.

        !!! danger "This will most likely break things at some point"
            If you go this route, just ensure you aren't using Nautical for anything mission critical, and be prepared to either help troubleshoot or wait for a new version with a bug fix.

        This is an example of using [Watchtower](https://github.com/containrrr/watchtower/) to keep Nautical on the `latest` version.
        
        === "Docker Compose"
            ```yaml hl_lines="3"
            ------8<------ "docker-compose-example.yml:3:4"
                image: minituff/nautical-backup:latest
            ------8<------ "docker-compose-example.yml:6:10"
              
              watchtower:
                image: containrrr/watchtower:latest
                container_name: watchtower
                volumes:
                  - /var/run/docker.sock:/var/run/docker.sock
                command: nautical-backup # (9)! 
            ```

            ------8<------ "docker-example-tooltips.md"
            1. Which containers to use. 

                Remove this line to update all contianers.

        === "Docker Cli"
            ```bash  hl_lines="6"
            ------8<------ "docker-run-example.sh::6"
              minituff/nautical-backup:latest
            
            docker run -d \
              --name watchtower \
              -v /var/run/docker.sock:/var/run/docker.sock \
              containrrr/watchtower \
              nautical-backup #(9)!
            ```

            ------8<------ "docker-example-tooltips.md"
            2. Which containers to use. 

                Remove this line to update all contianers.


