from cherrypy.process import wspbus, plugins
from modules.serialobject import SerialInterface
from serial import SerialException

class SerialObjectPlugin(plugins.SimplePlugin):
    def __init__(self, portname, bus):
        plugins.SimplePlugin.__init__(self, bus)
        self.serial = SerialInterface(portname)

    def start(self):
        self.bus.log('Instantiating serial object plugin')
        # self.bus.subscribe("plugin-test", self.test)
        self.bus.subscribe("serial-connect", self.connect)
        self.bus.subscribe("serial-disconnect", self.disconnect)
        self.bus.subscribe("serial-isconnected", self.is_connected)
        self.bus.subscribe("serial-write", self.serial_write)

    def stop(self):
        self.bus.log('Deleting serial object plugin')
        # self.bus.unsubscribe("serial-disconnect", self.disconnect)

    def connect(self):
        result = self.serial.connect()
        self.bus.log(result[1])
        if result[0]:
            _ = self.bus.publish('serial-just-connected')
        return result[0]

    def disconnect(self):
        result = self.serial.disconnect()
        self.bus.log(result[1])
        return result[0]

    def is_connected(self):
        return self.serial.is_connected()

    def serial_write(self, data):
        try:
            if len(data) > 1:
                result = self.serial.serial_write(data[0], data[1:])
            else:
                result = self.serial.serial_write(data[0], [])
        except (ValueError, SerialException, AttributeError) as e:
            self.bus.log('ERROR ' + str(e))
            return {'success':False,'data':None,'info':str(e)}
        return {'success':True,'data':result,'info':None}

    # def test(self, str=''):
    #     self.bus.log(str)
    #     return str
