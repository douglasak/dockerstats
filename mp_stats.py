import docker
import multiprocessing as mp
import json

output = mp.Queue()
client=docker.from_env()

container_names = []
container_stats = {}

for container in client.containers.list():
  container_names.append(container.name)

def docker_stats(server):
	client_lowlevel = docker.APIClient(base_url='unix://var/run/docker.sock')
	client_stats=client_lowlevel.stats(container=server,decode=False,stream=False)
	output.put(client_stats)

processes = [mp.Process(target=docker_stats, args=(server,)) for server in container_names]

# Run processes
for p in processes:
	p.start()

# Exit the completed processes
for p in processes:
	p.join()

while output.empty() is False:
	result = output.get()
	container_stats[result["name"]] = result

print(container_stats)

# f = open('workfile', 'w')
# json.dump(container_stats, f)
# f.close()

