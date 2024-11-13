# homelab-docker-swarm

## JuiceFS

Install Docker plugin on each worker node

```bash
docker plugin install juicedata/juicefs:latest --alias juicefs --grant-all-permissions  # volume driver name in compose files are using the alias name "juicefs"
```
