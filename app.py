import os
import cherrypy
from modules.plugin_serialobject import SerialObjectPlugin
import argparse
import importlib
import pdb

cherrypy.config.update(
{'server.socket_host': os.getenv('IP', '0.0.0.0'),
'server.socket_port': int(os.getenv('PORT', 8080)),
})

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

    @cherrypy.expose
    def index(self):
        return open('public/ui.html')

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def is_connected(self):
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
    # TODO: add more options, like one for connecting to the serial device automatically
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--serialport", type=str, help="name of the port that the arduino is connected to", \
                        action="store", default='/dev/ttyACM0')
    args = parser.parse_args()
    SerialObjectPlugin(args.serialport, cherrypy.engine).subscribe()
    args = None
    parser = None
    webapp = Controller()
    cherrypy.quickstart(webapp, '/', conf)
