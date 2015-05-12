import pyfirmata
import time

REPORT_ANALOG_NOW_QUERY = 0x01    # SysEx command code to request an analog report once
REPORT_ANALOG_NOW_RESPONSE = 0x02    # SysEx command code in response to the matching query

class Arduino:

    def __init__(self, port):
        self.board = None
        self.port = port
        self.iterthread = None
        _ = self.connect()
        self.commands = {
            'vset': {'params': 3, 'fun': self._vset},
            'vread': {'params': 1, 'fun': self._vread}}

    def __del__(self):
        self.disconnect()

    def connect(self):
        try:
            board = None
            board = pyfirmata.Arduino(self.port)

            board.add_cmd_handler(REPORT_ANALOG_NOW_RESPONSE)
        except Exception as e:
            if board:
                board.exit()
            return False, str(e)
        else:
            # initialize used PWM pins to zero volts
            for i in (3, 9, 10, 11):
                board.digital[i].mode = pyfirmata.PWM
                board.digital[i].write(0.0)
            self.board = board
            return True, 'Serial object connection successful'

    def disconnect(self):
        if self.board:
            # send a reset command
            self.reset()
            self.board.exit()
            self.board = None
            self.iterthread = None
            return True, 'Serial object disconnection successful'
        else:
            return False, 'Serial object already disconnected'

    def reconnect(self):
        _ = self.disconnect()
        return self.connect()

    def is_connected(self):
        return True if self.board else False

    def reset(self):
        self.board.sp.write(bytearray([pyfirmata.SYSTEM_RESET]))

    def serial_write(self, cmd=None, params=None):
        """This is the generic function used to send data to the Arduino.

        Returns:
            None or any value read.
        """
        if cmd not in self.commands:
            raise ValueError('Unexpected command: {}'.format(cmd))
        if self.commands[cmd]['params'] != len(params):
            raise ValueError('Expected {} params, got {}'.format(
                self.commands[cmd]['params'], len(params)))

        return self.commands[cmd]['fun'](params)

    def sampling_interval(self, milis):
        # minimum sampling interval supported is 10ms
        if milis > 16383:
            milis = 16383
        self.board.send_sysex(pyfirmata.SAMPLING_INTERVAL,
                              bytearray([milis % 128, milis >> 7]))

    def _vset(self, pins, values, settling):
        """Quickly send PWM values to the board.

        Args:
            pins (int list): any combination of (3,9,10,11)
            values (float list): in the range 0..1, corresponding to the pins list
            settling (int): milis to wait
        """
        for pin, value in zip(pins, values):
            self.board.digital[pin].write(value)
        time.sleep(settling/1000)

    # def _vread(self, pins):
    #     """Quickly read analog values from the board.
    #
    #     NOTE: reporting must first be enabled so that the values are refreshed.
    #
    #     Args:
    #         pins (int list): any combination of (0,1,2,3,4,5)
    #     Returns:
    #         list of float values in the range 0..1, corresponding to the pin list
    #     """
    #     result = []
    #     for pin in pins:
    #         result.append(self.board.analog[pin].read())
    #     return result

    def _vread(self, pins):
        """Conveniently read analog values from the board.

        This function is much more robust than having to rely on the utility
        thread that periodically runs board.iterate(), since an analog read I/O
        message does not signal it's completion, and therefore in cases where
        there is a high load on the CPU or the serial connection, the usual
        waiting time for the values to refresh might not be sufficient. However,
        with a shared counter `_vread_count` and a custom SysEx command with its
        corresponding handling function `_handle_report_analog_now`, the
        update of the values can be tracked and hence the successful execution
        of the command. This way meaningful analog values that truly represent
        reality at the current state are ensured.

        Args:
            pins (int list): any combination of (0,1,2,3,4,5)
        Returns:
            None or float list: values in the range 0..1, corresponding to the
            pin list, or None if the update wasn't received before 0.1s
        """
        result = []
        self._vread_done = False
        bwpins = 0
        for pin in pins:
            bwpins |= 1 << pin
        self.board.send_sysex(REPORT_ANALOG_NOW_QUERY, bytes((bwpins,)))
        status = 0
        before = time.time()
        while time.time() - before < 0.1:
            time.sleep(0.001)
            if not self.iterthread:
                self.board.iterate()
            if self._vread_done:
                status = 1
                break
        if status == 0:
            return None
        for pin in pins:
            result.append(self.board.analog[pin].read())
        return result

    def _handle_report_analog_now(self, *args, **kwargs):
        for i in range(0, len(args), 3):
            pin, lsb, msb = args[i], args[i+1], args[i+2]
            value = round(float((msb << 7) + lsb) / 1023, 4)
            self.board.analog[pin].value = value
        self._vread_done = True

    def enable_reporting(self, sampling=1000):
        """Enable reporting of all the analog pins. Without running this
        function first, the values returned by vread() will remain unchanged."""
        # start reader thread to catch reported values
        # the thread only stops when the serial connection is closed
        it = pyfirmata.util.Iterator(board)
        it.start()
        self.iterthread = it

        for pin in (0,1,2,3,4,5):
            self.board.analog[pin].enable_reporting()

        self.sampling_interval(sampling)

    def _vsweep(out_pins, in_pins, out_values, settling):
        """Perform a sweep of voltages. Reporting must be enabled to read meaningful data.

        Args:
            out_pins (int list): example: (3,9)
            in_pins (int list): pins to read from. Example: (0,1)
            out_values (list of float lists): float list for each out_pin. Example: ((0.0, 0.5, 1.0), (0.1, 0.2, 0.3))
            settling (int): milis to wait

        Returns:
            [step1:[p1 p2 ...], step2:[p1 p2 ...], ...] In other words, a list of steps, where each step is a list of the values on each pin
        """
        results = []
        # iterate over the values, zipping them for convenience
        for vals in zip(out_values):
            # write the values to the board one pin at a time
            for i, pin in enumerate(out_pins):
                self.board.digital[pin].write(vals[i])
            # wait for settling time after all pins are written
            time.sleep(settling/1000)
            # collect the readings of the current step
            step = []
            for pin in in_pins:
                step.append(self.board.analog[pin].read())
            # append the steps together
            results.append(step)
        return results
