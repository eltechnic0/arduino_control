import os, os.path
from time import time, sleep
from serial import Serial, SerialException
import cherrypy
import pdb
from plugin_serialobject import SerialObjectPlugin
# import plugin_serialobject

serialPort = '/dev/ttyACM0'
serialObject = None

cherrypy.config.update(
{'server.socket_host': os.getenv('IP', '0.0.0.0'),
'server.socket_port': int(os.getenv('PORT', 8080)),
})

# def isconnected():
#     # print('\nisconnected func\n')
#     # pdb.set_trace()
#     # instance = cherrypy.serving.request.handler.callable.__self__
#     # if not instance.serialObject:
#     # self = args[0]
#     global serialObject
#     if not serialObject:
#         # print('\nno serialObject\n')
#         # # supress normal handler
#         # return True
#         raise cherrypy.HTTPError("403 Forbidden",
#             "The serial object is disconnected.")
#     # allow normal handler
#     # print('serialObject')
#     # return False

def isconnected():
    global serialObject
    if not serialObject:
        cherrypy.response.status = 200
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        cherrypy.response.body = [b"The serial object is disconnected."]
        # print('\n')
        # print(cherrypy.response.status, end='\n')
        # print(cherrypy.response.headers, end='\n')
        # print(cherrypy.response.body, end='\n')

        # supress normal handler
        return True

# cherrypy.tools.isconnected = cherrypy._cptools.Tool('before_handler', isconnected)
cherrypy.tools.isconnected = cherrypy._cptools.HandlerTool(isconnected)

class Controller(object):

    # serialObject = None

    # def __init__(self):
    #     serialObject = None
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def testplugin(self, str='Hello world!'):
        return cherrypy.engine.publish('plugin-test', str)

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def serialtest(self):
        return cherrypy.engine.publish('serial-isconnected')

    @cherrypy.expose
    def index(self):
        return open('public/ui.html')

    @cherrypy.expose
    def connect(self):
        global serialObject
        try:
            serialObject = Serial(baudrate=9600, timeout=5)
            serialObject.port = serialPort
            serialObject.open()
        except SerialException as err:
            result = 'Disconnected - Connection error'
            serialObject = None
            print(err)
        else:
            result = 'Connected'
        return result

    @cherrypy.expose
    def disconnect(self):
        global serialObject
        if serialObject:
            serialObject.close()
            serialObject = None
        return "Disconnected"

    @cherrypy.expose
    def reconnect(self):
        aux = self.disconnect()
        aux = self.connect()
        return aux

    @cherrypy.expose
    @cherrypy.tools.isconnected()
    @cherrypy.tools.json_out()
    def serialComtest(self):
        self.serialWrite('comtest\n')
        return list(self.serialReadResponse())

    @cherrypy.expose
    @cherrypy.tools.isconnected()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def serialVSet(self):
        # pins and values are lists
        json = cherrypy.request.json
        pins = json['pins']
        values = json['values']
        settling = json['settling']

        if not pins or not values:
            return "No pins or values"
        if not isinstance(pins, list):
            return "No pin list"
        if not isinstance(values, list):
            return "No value list"
        if len(pins) != len(values):
            return "Inconsistent input data"

        for i in range(len(pins)):
            pin = pins[i]
            value = values[i]
            if pin not in (3,9,10,11):
                # invalid pin
                _unused = list(self.serialReadResponse(i))
                return "Invalid pin: {}".format(pin)
            if value > 255 or value < 0:
                # invalid value
                _unused = list(self.serialReadResponse(i))
                return "Invalid value: {}".format(value)
            value = int(value)
            if i == len(pins) - 1:
                # for the last one only - non zero settling
                string = 'vset\n{}\n{}\n{}\n'.format(pin, value, settling)
            else:
                string = 'vset\n{}\n{}\n0\n'.format(pin, value, settling)
            self.serialWrite(string)

        return list(self.serialReadResponse(i+1))

    @cherrypy.expose
    @cherrypy.tools.isconnected()
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def serialVRead(self):
        pins = cherrypy.request.json['pins']
        if not pins:
            return "No pins"
        i = 0
        for pin in pins:
            if pin not in (0,1,2,3,4,5):
                # Invalid pin
                continue
            i += 1
            string = 'vread\n{}\n'.format(pin)
            self.serialWrite(string)
        return list(self.serialReadResponse(i))

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def serialVerbose(self, value='true'):
        value = 1 if value == 'true' else 0
        self.serialWrite('verbose\n{}\n'.format(value))
        return list(self.serialReadResponse())

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def isConnected(self):
        global serialObject
        return True if serialObject else False

    def serialWrite(self, string):
        global serialObject
        serialObject.write(string.encode('utf-8'))

    def serialReadResponse(self, number=1):
        global serialObject
        response = []
        data = []
        isdata = False
        timeout = 5     # in seconds, for each message
        i = 0;
        before = time()
        while i < number:
            res = serialObject.readline()
            if not res:
                return data, ["No response... :-("]
            res = res.decode('ascii', 'replace').strip()
            response.append(res)
            if res.startswith("OK:start"):
                isdata = True;
                continue
            if res.startswith("OK:ready"):
                yield {"data":data, "msg":response}
                i += 1
                isdata = False;
                data = []
                response = []
                before = time()
                continue
            if isdata:
                data.append(res)
            if time() - before > timeout:
                return data, ["Timeout expired"]

    def __del__(self):
        self.disconnect()


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
    # print("Path is: " + os.path.abspath(os.getcwd()))
    SerialObjectPlugin(cherrypy.engine).subscribe()
    webapp = Controller()
    cherrypy.quickstart(webapp, '/', conf)
