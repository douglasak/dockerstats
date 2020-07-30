# dockerstats
Basic web dashboard of docker containers written in Python

Sample docker-compose file:

```
version: "2.1"
services:
  dockerstats:
    build: .
    container_name: dockerstats
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /volume1/docker/dockerstats:/usr/src/app
    restart: unless-stopped
```
