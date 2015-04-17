from cherrypy.process import wspbus, plugins

class SerialObjectPlugin(plugins.SimplePlugin):
    def __init__(self, bus):
        plugins.SimplePlugin.__init__(self, bus)
        from app import serialPort, serialObject
        global serialPort
        self.serialPort = serialPort
        global serialObject
        self.serialObject = serialObject

    def start(self):
        self.bus.log('Instantiating serial object')
        self.bus.subscribe("serial-connect", self.connect)
        self.bus.subscribe("plugin-test", self.test)
        self.bus.subscribe("serial-isconnected", self.isconnected)

    def stop(self):
        self.bus.log('Deleting serial object')
        self.bus.unsubscribe("serial-disconnect", self.disconnect)

    def connect(self):
        self.bus.log('Serial object connection successful')

    def disconnect(self):
        self.bus.log('Serial object disconnection successful')

    def test(self, str=''):
        self.bus.log(str)
        return str

    def isconnected(self):
        return True if self.serialObject else False
