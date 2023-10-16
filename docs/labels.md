Docker Labels allow us to apply settings to Nautical on a per-container basis. Instead of applying [enviornment variables](./arguments.md), we can apply the label to the each container seperately.

## Enable Nautical
With the [Require Label](./arguments.md#require-label) enviornment variable set to `true`, then all containers will be skipped unless they have this label.

> **Default If Missing**: true

```properties
nautical-backup.enable=false
```

If the [Require Label](./arguments.md#require-label) enviornment variable is *missing* or set to `false`, then [this label](#enable-nautical) will not be needed since the container will be backed up anyway.

## Skip
Skip any containers completely if this label is present.

> **Default If Missing**: false

```properties
nautical-backup.skip=true
```

## Stop Before Backup
Similar to the [Skip Stopping Containers](./arguments.md#skip-stopping-containers) variable. 
With this label applied, the container will not be stopped before performing a backup.

> **Default If Missing**: false

```properties
nautical-backup.stop-before-backup=true
```