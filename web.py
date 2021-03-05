import tornado.ioloop
import tornado.web
import tornado.template

import docker
#import yaml
import multiprocessing as mp

import time
import os
import configparser
from dateutil.parser import parse

client = docker.from_env()
loader = tornado.template.Loader("./templates")

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        attributes = get_attrs()
        self.write(loader.load("table.html").generate(attributes=attributes,memory=sum_memory(attributes),server_memory=server_memory()))

    def write_error(self, status_code, **kwargs):
        self.write("Status Code %d" % (status_code) + "\n<br>")
        self.write('kwargs: {}'.format(kwargs["exc_info"]))

class StatsHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(get_stats())

class InfoHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(client.info())

class ClientStatsHandler(tornado.web.RequestHandler):
    def get(self):
        container_name = self.get_argument("container")
        container = client.containers.get(container_name)
        self.write(container.stats(stream=False))

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

class LogsHandler(tornado.web.RequestHandler):
    def get(self):
        container_name = self.get_argument("container")
        container = client.containers.get(container_name)
        self.write(loader.load("logs.html").generate(name=container_name,logs=container.logs(timestamps=True)))

class TopHandler(tornado.web.RequestHandler):
    def get(self):
        container_name= self.get_argument("container")
        container = client.containers.get(container_name)
        self.write(loader.load("top.html").generate(name=container_name,top=container.top()))

class OutputHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(get_attrs())

class AttrsHandler(tornado.web.RequestHandler):
    def get(self):
        container_name= self.get_argument("container")
        container = client.containers.get(container_name)
        self.write(container.attrs)

class URHandler(tornado.web.RequestHandler):
    def get(self):
        cpuload = configparser.ConfigParser()
        cpuload.read('/emhttp/cpuload.ini')
        disk_file = open("/emhttp/disks.ini", "r")
        disk_info = disk_file.read().replace("\"","")
        disks = configparser.ConfigParser()
        disks.read_string(disk_info)
        cache_lbas = int(os.popen("cat /emhttp/smart/cache | grep '241 Total_LBAs_Written' | grep -Eo '[0-9]+$' | tr -d '\n'").read())
        tot_m, used_m, free_m = map(int, os.popen('free -t -m').readlines()[-1].split()[1:])
        uptime = float(os.popen("awk '{print $1}' /proc/uptime | tr -d '\n'").read())
        cpu_temp = float(os.popen("cat /sys/class/thermal/thermal_zone2/temp | tr -d '\n'").read())/1000
        mb_temp = float(os.popen("cat /sys/class/thermal/thermal_zone0/temp | tr -d '\n'").read())/1000

        output = {
          "cpuload": cpuload._sections,
          "disks": disks._sections,
          "cache": {"lbas_written": cache_lbas},
          "memory": {"total": tot_m, "used": used_m, "free": free_m},
          "system": {"uptime": uptime, "cpu_temp": cpu_temp, "mb_temp": mb_temp}
        }
        self.write(output)

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/logs", LogsHandler),
        (r"/top", TopHandler),
        (r"/stats", StatsHandler),
        (r"/client_stats", ClientStatsHandler),
        (r"/output", OutputHandler),
        (r"/attrs", AttrsHandler),
        (r"/info", InfoHandler),
        (r"/ur", URHandler)
    ], debug=(os.environ.get('DEBUG') == 'true'))

def get_stats():
    output = mp.Queue()

    container_names = []
    container_stats = {}

    for container in client.containers.list():
        container_names.append(container.name)

    def docker_stats(server):
        client_lowlevel = docker.APIClient(base_url="unix://var/run/docker.sock")
        client_stats=client_lowlevel.stats(container=server,decode=False,stream=False)
        output.put(client_stats)

    processes = [mp.Process(target=docker_stats, args=(server,)) for server in container_names]

    for p in processes:
        p.start()

    for p in processes:
        p.join()

    while output.empty() is False:
        result = output.get()
        container_stats[result["name"][1:]] = result

    return container_stats

def get_attrs():
    container_attrs = {}
    container_stats = get_stats()

    for container in client.containers.list():
        image_name = container.image.attrs["RepoTags"][0]
        image_created = calc_age(container.image.attrs["Created"])
        container_created = calc_age(container.attrs["Created"])
        container_attrs[container.name] = { 
            "status": container.status, 
            "id": container.short_id, 
            "image": image_name, 
            "image_created": image_created,
            "container_created": container_created
        }

    for container in container_stats:
        container_attrs[container]["rss"] = container_stats[container]["memory_stats"]["stats"]["rss"]
        container_attrs[container]["limit"] = container_stats[container]["memory_stats"]["limit"]

    return container_attrs

def sum_memory(container_attrs):
    memory = 0
    for container in container_attrs:
        memory += container_attrs[container]["rss"]
    return memory

def calc_age(datetime):
    timestamp = parse(datetime).timestamp()

    return (time.time() - timestamp) / (3600*24)

def server_memory():
    #with open(r"./config.yaml") as file:
    #    return yaml.load(file, Loader=yaml.FullLoader)["server_memory"]
    return client.info()["MemTotal"]/(1024*1024*1024)

if __name__ == "__main__":
    app = make_app()
    app.listen(80)
    tornado.ioloop.IOLoop.current().start()