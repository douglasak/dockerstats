import tornado.ioloop
import tornado.web
import tornado.template

import docker
import multiprocessing as mp

client = docker.from_env()
loader = tornado.template.Loader("./templates")

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        containers = get_stats()
        #for container in sorted(containers):
        #    self.write(container + " " + "%d %d" % (containers[container]["memory_stats"]["usage"], containers[container]["memory_stats"]["limit"]) + "\n<br>")
        self.write(loader.load("table.html").generate(containers=containers))

    def write_error(self, status_code, **kwargs):
        self.write("Status Code %d" % (status_code) + "\n<br>")
        self.write('kwargs: {}'.format(kwargs["exc_info"]))

class StatsHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(get_stats())

class LogsHandler(tornado.web.RequestHandler):
    def get(self):
        container_name= self.get_argument("container")
        container = client.containers.get(container_name)
        #self.write(container.logs())
        self.write(loader.load("logs.html").generate(name=container_name,logs=container.logs(timestamps=True)))

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/logs", LogsHandler),
        (r"/stats", StatsHandler)
    ], debug=True)

def get_stats():
    output = mp.Queue()

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
        container_stats[result["name"][1:]] = result

    return container_stats

if __name__ == "__main__":
    app = make_app()
    app.listen(80)
    tornado.ioloop.IOLoop.current().start()