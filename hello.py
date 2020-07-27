import tornado.ioloop
import tornado.web

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

class StatsHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, stats")

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/stats", StatsHandler)
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(80)
    tornado.ioloop.IOLoop.current().start()