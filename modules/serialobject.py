from serial import Serial, SerialException
from time import time, sleep

class SerialInterface(object):
    """
    This is an interface class to the serial device for convenience. It relies
    on the custom communication protocol of the arduino code.
    The class checks for value correctness before sending data to the serial
    device.
    It works checking if the given command and params match any of the available
    commands in `self.commands`. If so, calls the corresponding private function
    that is stored in self.commands[cmd]['fun'] where `cmd` is the requested
    command.

    ValueError exceptions are designed to raise before any data is writen to the
     serial device to avoid changing state when the message is wrong.

    The main usable functions are `serial_write`, `connect`, `disconnect` and
    `is_connected`.
    """
    def __init__(self, portname=None, baudrate=9600, timeout=5):
        if not portname:
            raise SerialException('No port name given')
        self.portname = portname
        self.baudrate = baudrate
        self.timeout = timeout
        self.serialObject = None
        self.commands = {
            'comtest':{'params':0,'fun':self._comtest},
            'vread':{'params':1,'fun':self._vread,'pins':(0,1,2,3,4,5)},
            'vset':{'params':3,'fun':self._vset,'pins':(3,9,10,11)},
            'verbose':{'params':1,'fun':self._verbose}}

    def serial_write(self, cmd=None, params=None):
        """
        This is the function used to send data to the Arduino. It returns the
        data read in the format [[data],[msg]]. More info in the `_read_response`
        function.
        """
        if cmd not in self.commands:
            raise ValueError('Unexpected command: {}'.format(cmd))
        if self.commands[cmd]['params'] != len(params):
            raise ValueError('Expected {} params, got {}'.format(\
                self.commands[cmd]['params'], len(params)))
        numreads = self.commands[cmd]['fun'](params)
        return list(self._read_response(numreads))

    def _comtest(self, params=None):
        bstring = b'comtest\n'
        self.serialObject.write(bstring)
        return 1

    def _vset(self, params):
        """
        :params format is [[pins],[vals],settling] and len(pins)==len(vals)
        """
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
        """
        Reads all lines until an `OK:ready` message, for `numreads` times.
        The data returned is [{"data":[data]|data,"msg":[msg]}], where data is the data returned between
        an `OK:start` and an `OK:ready`, and msg contains all lines read as list.
        A zero number of reads is allowed.
        """
        response = []
        data = []
        isdata = False
        timeout = self.timeout     # in seconds, for each message
        i = 0;
        before = time()
        while i < numreads:
            res = self.serialObject.readline()
            if not res:
                return {"data":data, "msg":["No response... :-("]}
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
                return {"data":data, "msg":["Timeout expired"]}

    def connect(self, timeout=0.1):
        """
        Connect to the Arduino and return only when it is ready.
        Returns (success, msg), where `success` is a boolean and `msg` a string
        with the description of the outcome.
        """
        # Minimum timeout for good behavior
        timeout = max(timeout, 0.02)
        try:
            self.serialObject = Serial(baudrate=self.baudrate, timeout=timeout)
            self.serialObject.port = self.portname
            self.serialObject.open()
        except SerialException as exc:
            self.serialObject = None
            return False, str(exc)
        else:
            # No error. Now send and read every 0.2s until getting a response
            before = time()
            success = False
            while time()-before < self.timeout:
                _ = self._comtest()
                result = self.serialObject.readline()
                if result:
                    # Make sure the buffer is cleared
                    sleep(timeout)
                    self.serialObject.flushInput()
                    success = True
                    break
            if not success:
                self.serialObject.close()
                self.serialObject = None
                return False, 'ERROR: connected but getting no response before \
                    a timeout of {}s'.format(self.timeout)
        # Set normal timeout
        self.serialObject.timeout = self.timeout
        return True, 'Serial object connection successful'

    def disconnect(self):
        if not self.serialObject:
            return False, 'Serial object already disconnected'
        try:
            self.serialObject.close()
        except SerialException as exc:
            self.serialObject = None
            return False, str(exc)
        self.serialObject = None
        return True, 'Serial object disconnection successful'

    def is_connected(self):
        return True if self.serialObject else False

    def __del__(self):
        _ = self.disconnect()
