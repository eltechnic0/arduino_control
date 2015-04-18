import os
import cherrypy
from modules.plugin_serialobject import SerialObjectPlugin
import argparse
import importlib
import pdb

def is_connected():
    serialObject = cherrypy.engine.publish('serial-isconnected')[0]
    if not serialObject:
        cherrypy.response.status = 200
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        cherrypy.response.body = [b"The serial object is disconnected."]
        # supress normal handler
        return True

cherrypy.tools.is_connected = cherrypy._cptools.HandlerTool(is_connected)

class Controller(object):

    def __init__(self, quickstart=False, verbose=True):
        if quickstart:
            cherrypy.engine.subscribe('start',
                lambda: cherrypy.engine.publish('serial-connect')[0])
        if not verbose and quickstart:
            cherrypy.engine.subscribe('start',
                lambda: cherrypy.engine.publish(
                    'serial-write', ['verbose', 0])[0])

    @cherrypy.expose
    def index(self):
        return open('public/ui.html')

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def isConnected(self):
        result = cherrypy.engine.publish('serial-isconnected')[0]
        return True if result else False

    @cherrypy.expose
    def connect(self):
        result = cherrypy.engine.publish('serial-connect')[0]
        if not result:
            result = 'Disconnected - Connection error'
        else:
            result = 'Connected'
        return result

    @cherrypy.expose
    def disconnect(self):
        _ = cherrypy.engine.publish('serial-disconnect')[0]
        return 'Disconnected'

    @cherrypy.expose
    def reconnect(self):
        result = self.disconnect()
        result = self.connect()
        return result

    @cherrypy.expose
    @cherrypy.tools.is_connected()
    @cherrypy.tools.json_out()
    def serialComtest(self):
        aux = cherrypy.engine.publish('serial-write', ['comtest'])[0]
        return aux

    @cherrypy.expose
    @cherrypy.tools.is_connected()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def serialVSet(self):
        # pins and values are lists
        json = cherrypy.request.json
        pins = json['pins']
        values = json['values']
        settling = json['settling']
        return cherrypy.engine.publish('serial-write', ['vset',pins,values,settling])[0]

    @cherrypy.expose
    @cherrypy.tools.is_connected()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def serialVRead(self):
        pins = cherrypy.request.json['pins']
        return cherrypy.engine.publish('serial-write', ['vread',pins])[0]

    @cherrypy.expose
    @cherrypy.tools.is_connected()
    @cherrypy.tools.json_out()
    def serialVerbosity(self, value='true'):
        value = 1 if value == 'true' else 0
        result = cherrypy.engine.publish('serial-write', ['verbose',value])[0]
        return result

    @cherrypy.expose
    @cherrypy.tools.is_connected()
    @cherrypy.tools.json_out()
    def serialScript(self, fname=None, **kwargs):
        try:
            module = importlib.import_module('scripts.'+fname)
            script = module.AppScript(cherrypy)
        except (ImportError, AttributeError) as exc:
            cherrypy.engine.log('ERROR '+str(exc))
            result = 'Error importing the script'
        else:
            try:
                result = script.run(**kwargs)
            except Exception as exc:
                cherrypy.engine.log('ERROR '+str(exc))
                result = 'Error running the script'
        return result

    def __del__(self):
        _ = self.disconnect()


if __name__ == '__main__':
    conf = {
        # 'global': {
        #     'engine.autoreload.on': False
        # },
        '/': {
            'tools.staticdir.root': os.path.abspath(os.getcwd()),
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './public'
        }
    }
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--serialport", type=str, default='/dev/ttyACM0',
        help="name of the port that the arduino is connected to", action="store")
    parser.add_argument("-c", "--connect", action="store_true", default=False,
        help="connect to the serial device immediately")
    parser.add_argument("-p", "--port", type=int, action="store", default=8080,
        help="port number for the web server")
    parser.add_argument("-v", "--verbose", action="store_true", default=False,
        help="verbose communication. Only works when the --connect flag is given. \
            Otherwise verbose output is enabled")
    args = parser.parse_args()
    # IP 0.0.0.0 accepts all incoming ips on the given port
    cherrypy.config.update(
    {'server.socket_host': os.getenv('IP', '0.0.0.0'),
    'server.socket_port': int(os.getenv('PORT', args.port)),
    })
    SerialObjectPlugin(args.serialport, cherrypy.engine).subscribe()
    webapp = Controller(quickstart=args.connect, verbose=args.verbose)
    # Delete parser object
    args = None
    parser = None
    # Start web app
    cherrypy.quickstart(webapp, '/', conf)
