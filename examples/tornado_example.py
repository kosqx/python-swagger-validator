#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tornado.ioloop
import tornado.web
import tornado.httpserver

import json

import types
tornado.web.RequestHandler.old_finish = tornado.web.RequestHandler.finish

def new_finish(self, value=''):
    print 'new_finish'
    self.qx_returned_value = value
    self.old_finish(value)
tornado.web.RequestHandler.finish = new_finish

class MainHandler(tornado.web.RequestHandler):
    def __init__(self, *args, **kwargs):
        # print '__init__', args, kwargs
        # print
        super(MainHandler, self).__init__(*args, **kwargs)

    def get(self):
        #self.write("Hello, world")
        self.finish("Hello, world")

def log(handler):
    print
    print 'log_function', handler
    print dir(handler)
    print handler.request.request_time()
    print dir(handler.request)
    print 

application = tornado.web.Application([
    (r"/", MainHandler),
],
    autoreload=True,
    #log_function=log,
)



def middleware(request):
    # do whatever transformation you want here
    print 'dir(request)', dir(request)
    print {''}

    print '_' * 100
    r = {'method': request.method, 'path': request.path, 'headers': request.headers, 'query': request.query, 'query_arguments': request.query_arguments}
    print json.dumps(r, sort_keys=True, indent=4)
    print '^' * 100

    result = application(request)
    print dir(application)
    print application.transforms, application.ui_methods, application.ui_modules
    print 'result', result
    print 'result.value', result.qx_returned_value
    return result

if __name__ == "__main__":
    #application.listen(8888)
    http_server = tornado.httpserver.HTTPServer(middleware)
    http_server.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
