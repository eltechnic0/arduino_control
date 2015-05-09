import os
import cherrypy
from modules.plugin_serialobject import SerialObjectPlugin
from modules.makotool import TemplateTool
import argparse
import importlib
import json


def is_connected():
    """
    Prehandler for methods that write to the Arduino. Checks if the device is
    connected and prevents the normal handler to run if it is disconnected.
    """
    serialObject = cherrypy.engine.publish('serial-isconnected')[0]
    if not serialObject:
        cherrypy.response.status = 200
        # cherrypy.response.headers['Content-Type'] = 'text/plain'
        cherrypy.response.headers['Content-Type'] = 'application/json'
        result = {'success': False, 'info': 'The serial object is disconnected'}
        result = json.dumps(result).encode('utf-8')
        cherrypy.response.body = result
        # cherrypy.response.body = [b"The serial object is disconnected."]
        # supress normal handler
        return True

path = os.path.abspath(os.getcwd())
cherrypy.tools.is_connected = cherrypy._cptools.HandlerTool(is_connected)
cherrypy.tools.render = TemplateTool(path)


class Controller(object):

    def __init__(self, quickstart=False, verbose=False):
        # Search for addons as folders inside the addons folder, and take the
        # first non '__init__.py' file. Builds a list of addons' info and mounts
        # them into the server tree
        addons = []
        for parent in os.listdir('addons/'):
            for file in os.listdir(os.path.join('addons/', parent)):
                # only one file allowed for each addon currently
                isnotinit = file != '__init__.py'
                isaddon = file.find('addon_') != -1
                isaddon = isaddon and file.find('.py') != -1
                if isnotinit and isaddon:
                    name, _ = file.split('.')
                    module = importlib.import_module('.'.join(['addons',
                                                              parent,
                                                              name]))
                    addon = module.AppAddon()
                    cherrypy.tree.mount(addon,
                                        addon.addon_conf['url'],
                                        addon.cpconf)
                    addons.append(addon.addon_conf)
                    break
        self.addons = addons

        # Subscribe to the start channel to connect and disable verbosity when
        # the server is ready
        if quickstart:
            cherrypy.engine.subscribe(
                'start',
                lambda: cherrypy.engine.publish('serial-connect')[0])
        if not verbose:
            cherrypy.engine.subscribe(
                'serial-just-connected',
                lambda: cherrypy.engine.publish(
                    'serial-write', ['verbose', 0])[0])

    @cherrypy.expose
    @cherrypy.tools.render(name='ui.mako')
    def index(self):
        return {'addons': self.addons}

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
        return cherrypy.engine.publish(
                    'serial-write',
                    ['vset', pins, values, settling])[0]

    @cherrypy.expose
    @cherrypy.tools.is_connected()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def serialVRead(self):
        pins = cherrypy.request.json['pins']
        return cherrypy.engine.publish('serial-write', ['vread', pins])[0]

    @cherrypy.expose
    @cherrypy.tools.is_connected()
    @cherrypy.tools.json_out()
    def serialVerbose(self, value='true'):
        value = 1 if value == 'true' else 0
        result = cherrypy.engine.publish('serial-write', ['verbose', value])[0]
        return result

    @cherrypy.expose
    @cherrypy.tools.is_connected()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def serialScript(self):
        """
        Takes json input {"fname":script_name,**kwargs}
        Returns [success:bool, msg:str]
        """
        fname = cherrypy.request.json['fname']
        kwargs = {k: v for k, v in cherrypy.request.json.items()
                  if k != 'fname'}
        try:
            module = importlib.import_module('addons.scripts.'+fname)
            script = module.AppScript(cherrypy)
        except (ImportError, AttributeError) as exc:
            cherrypy.engine.log('ERROR '+str(exc))
            msg = 'Error importing the script'
            result = {'success': False, 'info': msg}
        else:
            try:
                # Should not return anything for now
                data = script.run(**kwargs)
            except Exception as exc:
                cherrypy.engine.log('ERROR '+str(exc))
                msg = 'Error running the script'
                result = {'success': False, 'info': msg}
            else:
                msg = 'Script {} run successfully'.format(fname)
                result = {'success': True, 'info': msg, 'data': data}
        return result

    def __del__(self):
        _ = self.disconnect()


if __name__ == '__main__':
    conf = {
        # 'global': {
        #     'engine.autoreload.on': False
        # },
        '/': {
            'tools.staticdir.root': path,
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'static'
        }
    }
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s", "--serialport", type=str, default='/dev/ttyACM0', action="store",
        help="name of the port that the arduino is connected to")
    parser.add_argument(
        "-c", "--connect", action="store_true", default=False,
        help="connect to the serial device immediately")
    parser.add_argument(
        "-p", "--port", type=int, action="store", default=8081,
        help="port number for the web server")
    parser.add_argument(
        "-v", "--verbose", action="store_true", default=False,
        help="verbose communication. Only works when the --connect flag is given. \
            Otherwise verbose output is enabled")
    args = parser.parse_args()

    # IP 0.0.0.0 accepts all incoming LAN ip's on the given port
    cherrypy.config.update(
        {'server.socket_host': os.getenv('IP', '0.0.0.0'),
         'server.socket_port': int(os.getenv('PORT', args.port)), })

    # Serialobject plugin and main app init
    SerialObjectPlugin(args.serialport, cherrypy.engine).subscribe()
    webapp = Controller(quickstart=args.connect, verbose=args.verbose)

    # Delete parser object
    args = None
    parser = None

    # Start web app
    cherrypy.quickstart(webapp, '/', conf)
