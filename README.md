# homelab-docker-swarm

## Setup shared Docker Swarm volumes with JuiceFS

> All the below steps MUST be executed **on each docker worker** once.

1. Install `juicefs` client.

    ```bash
    curl -sSL https://d.juicefs.com/install | sh -
    ```

2. Create credentials file.

    ```bash
    # create file
    cat << 'EOF' > /etc/default/juicefs
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
    # export MINIO variables on current shell
    export MINIO_REGION=$(awk -F'=' '/MINIO_REGION=/{print $2}' /etc/default/juicefs)
    export MINIO_HOST="https://s3.local:9000"  # example
    export MINIO_BUCKET="ds-data"  # example
    export MINIO_VOLUME="shared"  # example
    export MINIO_ACCESS_KEY="gHaFppe1PLHmaEKHHCe3"  # example
    export MINIO_SECRET_KEY="AsJFtOL7Cfku6vEun6r60pizKV0nxnESNFDidn9C"  # example

    # export JuiceFS variables on current shell
    export JFS_REDIS_USERNAME=$(awk -F'=' '/JFS_REDIS_USERNAME=/{print $2}' /etc/default/juicefs)
    export JFS_REDIS_PASSWORD=$(awk -F'=' '/JFS_REDIS_PASSWORD=/{print $2}' /etc/default/juicefs)
    export JFS_REDIS_HOST=$(awk -F'=' '/JFS_REDIS_HOST=/{print $2}' /etc/default/juicefs)
    export JFS_REDIS_PORT=$(awk -F'=' '/JFS_REDIS_PORT=/{print $2}' /etc/default/juicefs)

    # MINIO_ACCESS_KEY and MINIO_SECRET_KEY are placeholders
    juicefs format \
        --trash-days 0 \
        --storage minio \
        --bucket "${MINIO_HOST}/${MINIO_BUCKET}?tls-insecure-skip-verify=true" \
        --access-key "${MINIO_ACCESS_KEY}" \
        --secret-key "${MINIO_SECRET_KEY}" \
        "redis://${JFS_REDIS_USERNAME}:${JFS_REDIS_PASSWORD}@${JFS_REDIS_HOST}:${JFS_REDIS_PORT}/1" "${MINIO_VOLUME}"
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
