import docker

client = docker.from_env()

container_stats = {}
kwargs = {"stream": False}

for container in client.containers.list():
  container_stats[container.name] = ""

for x in container_stats:
  container = client.containers.get(x)
  container_stats[x] = container.stats(**kwargs)

print(container_stats)
