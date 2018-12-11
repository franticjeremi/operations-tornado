# coding: UTF-8
from tornado.ioloop import IOLoop
from tornado.web import Application, StaticFileHandler
from handlers import MainHandler, OperationsWebSocket


def make_app():
    return Application([
        (r"/", MainHandler),
        (r"/operation", OperationsWebSocket),
        (r'/static/(.*)', StaticFileHandler, {'path': 'static'})
    ])


if __name__ == '__main__':
    app = make_app()
    app.listen(8888)
    IOLoop.current().start()
