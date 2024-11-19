## Why?
The simple configuration is to pass the Docker socket straight into the Nautical container like this:

* `/var/run/docker.sock:/var/run/docker.sock`


However, giving access to your Docker socket could mean giving root access to your host. 
While Nautical needs *some* control of your Docker socket to inspect/start/stop/exec your containers, it does not need complete control.
Using the [Docker Socket Proxy](https://github.com/Tecnativa/docker-socket-proxy) allows you to remove permissions away from Nautical but still allow what's necessary.


## How?
We can use the [Docker Socket Proxy](https://github.com/Tecnativa/docker-socket-proxy) container to act as a *man-in-the-middle* (AKA Proxy) for the Docker socket.

Essentially, the [DSP](https://github.com/Tecnativa/docker-socket-proxy) gets full control over the Docker Socket, but it then gives out smaller permissions to the socket out to Nautical <small>(or anything else)</small>.

## Setup
For more information about which Docker Socket Proxy Enviornment varibles you must enable, check out [their docs](https://github.com/Tecnativa/docker-socket-proxy?tab=readme-ov-file#grant-or-revoke-access-to-certain-api-sections).

```yaml hl_lines="3 31"
services:
  # Establish the docker socket proxy
------8<------ "docker-socket-proxy.yml"

------8<------ "docker-compose-example-no-tooltips.yml:2:5"
      # Notice we removed the socket mount
------8<------ "docker-compose-example-no-tooltips.yml:7:10"
      # Enable the Proxy in Nautical
      # The name `docker_socket_proxy` must match the name of the service
      # And they must be in the same compose, unless you use the absolute URL
      - DOCKER_HOST=tcp://docker_socket_proxy:2375
```