import tornado.ioloop
import tornado.web
import tornado.wsgi

from Sendor import root as mainapp

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

mainapp.secret_key = 'why would I tell you my secret key?'
wsgi_app=tornado.wsgi.WSGIContainer(mainapp)

application = tornado.web.Application([
    (r"/tornado", MainHandler),
    ('.*', tornado.web.FallbackHandler, dict(fallback=wsgi_app)),
])

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
