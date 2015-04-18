from serial import Serial, SerialException
from time import time

class SerialInterface(object):
    """
    The class checks for value correctness before sending data to the serial device

    ValueError exceptions are designed to raise before any data is writen to the serial device
    """
    def __init__(self, portname=None, baudrate=9600):
        if not portname:
            raise SerialException('No port name given')
        self.portname = portname
        self.baudrate = baudrate
        self.serialObject = None
        self.commands = {
            'comtest':{'params':0,'fun':self._comtest},
            'vread':{'params':3,'fun':self._vread,'pins':(0,1,2,3,4,5)},
            'vset':{'params':3,'fun':self._vset,'pins':(3,9,10,11)},
            'verbose':{'params':1,'fun':self._verbose}}
        # self.commands = [
        #     {'keyword':'comtest','params':0,'fun':self._comtest},
        #     {'keyword':'vread','params':3,'fun':self._vread,'pins':(0,1,2,3,4,5)},
        #     {'keyword':'vset','params':3,'fun':self._vset,'pins':(3,9,10,11)},
        #     {'keyword':'verbose','params':1,'fun':self._verbose}]

    def serial_write(self, cmd=None, params=None):
        if cmd not in self.commands:
            raise ValueError('Unexpected command: {}'.format(cmd))
        if self.commands[cmd]['params'] != len(params):
            raise ValueError('Expected {} params, got {}'.format(\
                self.commands[cmd]['params'], len(params)))
        numreads = self.commands[cmd]['fun'](params)
        # ref = [x if x['keyword'] == cmd else None for x in self.commands]
        # if not ref:
        #     return []
        # ref = ref[0]
        # if ref['params'] != len(params):
        #     return []
        # fun = self.__dict__['_'+self.__name__ + '__'+cmd]
        # numreads = fun(self, params)
        # numreads = ref['fun'](params)
        return list(self._read_response(numreads))

    def _comtest(self, params):
        bstring = b'comtest\n'
        self.serialObject.write(bstring)
        return 1

    def _vset(self, params):
        """
        :params format is [[pins],[vals],settling] and len(pins)==len(vals)
        """
        # bstring = 'vset\n{}\n{}\n{}\n'.format(*params).encode('utf-8')
        # self.serialObject.write(bstring)
        pins, values, settling = params
        if len(pins) != len(values):
            raise ValueError('Inconsistent command')
        if any([x not in self.commands['vset']['pins'] for x in pins]):
            raise ValueError('Valid pins are: {}'.format(\
                self.commands['vset']['pins']))
        values = list(map(int, values))
        if any([x > 255 or x < 0 for x in values]):
            raise ValueError('Value range is 0-255')
        settling = int(settling)
        if settling < 0 or settling > 65535:
            raise ValueError('Settling range is 0-65535')
        for i in range(len(pins)):
            pin = pins[i]
            value = values[i]
            if i == len(pins) - 1:
                # for the last one only - non zero settling
                bstring = 'vset\n{}\n{}\n{}\n'.format(pin, value, settling)
            else:
                bstring = 'vset\n{}\n{}\n0\n'.format(pin, value, settling)
            bstring = bstring.encode('utf-8')
            self.serialObject.write(bstring)
        return i+1

    def _vread(self, params):
        """
        :params format is [[pins]]
        """
        pins = params[0]
        if any([x not in self.commands['vread']['pins'] for x in pins]):
            raise ValueError('Valid pins are: {}'.format(\
                self.commands['vread']['pins']))
        for i in range(len(pins)):
            bstring = 'vread\n{}\n'.format(pins[i]).encode('utf-8')
            self.serialObject.write(bstring)
        return i+1

    def _verbose(self, params):
        if params[0] not in (0,1):
            raise ValueError('Verbosity value {} is not 0 or 1'.format(params[0]))
        bstring = 'verbose\n{}\n'.format(params[0]).encode('utf-8')
        self.serialObject.write(bstring)
        return 1

    def _read_response(self, numreads=1):
        response = []
        data = []
        isdata = False
        timeout = 5     # in seconds, for each message
        i = 0;
        before = time()
        while i < numreads:
            res = self.serialObject.readline()
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

    def connect(self):
        try:
            self.serialObject = Serial(baudrate=self.baudrate, timeout=5)
            self.serialObject.port = self.portname
            self.serialObject.open()
        except SerialException as exc:
            self.serialObject = None
            # return False, 'Serial object connection error: '+str(exc)
            return False, 'ERROR: ' + str(exc)
        return True, 'Serial object connection successful'

    def disconnect(self):
        try:
            self.serialObject.close()
        except SerialException:
            self.serialObject = None
            return False, 'Serial object disconnection error'
        self.serialObject = None
        return True, 'Serial object disconnection successful'

    def is_connected(self):
        return True if self.serialObject else False
