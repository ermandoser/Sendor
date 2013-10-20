import tornado.ioloop
import tornado.web
import tornado.wsgi

from Sendor import root as mainapp
from SendorWS.sendorwshandler import WSHandler

mainapp.secret_key = 'why would I tell you my secret key?'
wsgi_app=tornado.wsgi.WSGIContainer(mainapp)

application = tornado.web.Application([
    (r"/ws", WSHandler),
    ('.*', tornado.web.FallbackHandler, dict(fallback=wsgi_app)),
])

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
