# Setup shared Docker volumes with JuiceFS

What is [JuiceFS](https://juicefs.com/docs/community/getting-started/for_distributed?ref=git.xtuxnet.com)? A High-Performance, Cloud-Native, Distributed File System.

> The below guide supports AWS and Minio S3 buckets.

## Prepare the hosts

> All the below steps MUST be executed **on each docker worker** once.

1. Install `juicefs` client.

    ```bash
    curl -sSL https://d.juicefs.com/install | sh -
    ```

2. Create credentials file.

    ```bash
    # create file
    cat << 'EOF' > /etc/default/juicefs
    S3_REGION=homelab
    AWS_REGION=homelab
    MINIO_REGION=homelab
    JFS_REDIS_USERNAME=redis
    JFS_REDIS_PASSWORD=redispass
    JFS_REDIS_HOST=redis.local
    JFS_REDIS_PORT=6379
    EOF

    # secure permissions
    chmod 0600 /etc/default/juicefs
    ```

3. It is highly recommended, to mount an extra SSD or NVMe disk for JuiceFS cache. In this guide, the default mountpoint for the cache is used: `/var/jfsCache`.

4. Format the JuiceFS volume.

    > Copy the bash snippet to a notepad and edit the exports before copy-pasting to Docker worker.
    >
    > This will create a Minio bucket named "**ds-data**" with a volume inside named "**shared**"

    ```bash
    # export variables to current shell
    export S3_REGION=$(awk -F'=' '/S3_REGION=/{print $2}' /etc/default/juicefs)
    export MINIO_REGION="${S3_REGION}"
    export AWS_REGION="${S3_REGION}"
    export S3_HOST="https://s3.local:9000"  # example
    export S3_BUCKET="ds-data"  # example
    export S3_VOLUME="shared"  # example
    export S3_ACCESS_KEY="gHaFppe1PLHmaEKHHCe3"  # example
    export S3_SECRET_KEY="AsJFtOL7Cfku6vEun6r60pizKV0nxnESNFDidn9C"  # example
    export JFS_REDIS_USERNAME=$(awk -F'=' '/JFS_REDIS_USERNAME=/{print $2}' /etc/default/juicefs)
    export JFS_REDIS_PASSWORD=$(awk -F'=' '/JFS_REDIS_PASSWORD=/{print $2}' /etc/default/juicefs)
    export JFS_REDIS_HOST=$(awk -F'=' '/JFS_REDIS_HOST=/{print $2}' /etc/default/juicefs)
    export JFS_REDIS_PORT=$(awk -F'=' '/JFS_REDIS_PORT=/{print $2}' /etc/default/juicefs)

    # do not worry, if you run it again it will not delete any previous data if not forced
    # replace "--storage minio" with "--storage s3" if the bucket is on AWS
    juicefs format \
        --trash-days 0 \
        --storage minio \
        --bucket "${S3_HOST}/${S3_BUCKET}?tls-insecure-skip-verify=true" \
        --access-key "${S3_ACCESS_KEY}" \
        --secret-key "${S3_SECRET_KEY}" \
        "redis://${JFS_REDIS_USERNAME}:${JFS_REDIS_PASSWORD}@${JFS_REDIS_HOST}:${JFS_REDIS_PORT}/1" "${S3_VOLUME}"
    ```

5. Create symlink for `mount.juicefs`.

    ```bash
    ln -s /usr/local/bin/juicefs /sbin/mount.juicefs
    ```

6. Generate a systemd mount, for Docker to use as bind-volume.

    > This enables concurrent reads and writes on Docker volumes and ensures persistence on host

    ```bash
    cat <<- EOF > "/etc/systemd/system/juicefs.mount"
    [Unit]
    Description=JuiceFS mountpoint
    Before=docker.service

    [Mount]
    EnvironmentFile=-/etc/default/juicefs
    What=redis://\${JFS_REDIS_USERNAME}:\${JFS_REDIS_PASSWORD}@\${JFS_REDIS_HOST}:\${JFS_REDIS_PORT}/1
    Where=/juicefs
    Type=juicefs
    Options=_netdev,allow_other,backup-skip-trash,enable-xattr,no-usage-report,writeback

    [Install]
    WantedBy=remote-fs.target
    EOF

    # enable and re/start mountpoint
    systemctl enable juicefs.mount
    systemctl restart juicefs.mount
    ```

## Deploy services

On your docker compose, just utilize docker bind volumes to mount the previously mounted JuiceFS share into the containers. It is highly recommended to create subdirectories to isolate different services that require different permissions and security practices.

For example:

```yml
services:
  coolservice:
    image: "cool-example/service-example:latest"
    volumes:
      - "/juicefs/services/coolservice/data:/data"
      - "/juicefs/common:/common:ro"
```

> Yeap, that easy
