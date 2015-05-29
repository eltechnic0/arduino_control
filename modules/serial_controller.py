import pyfirmata
import time

REPORT_ANALOG_NOW_QUERY = 0x01    # SysEx command code to request an analog report once
REPORT_ANALOG_NOW_RESPONSE = 0x02    # SysEx command code in response to the matching query

class Arduino:

    def __init__(self, port, hiz_mode=False):
        """Initialize and connect to the board.

        New commands should be registered in the commands dict.

        Args:
            port (str): port name to give to the serial object. Usually 'COM3' on Windows, and '/dev/ttyACM0' or similar on Linux
            hiz_mode (bool): whether to treat a 0V output as HI-Z by default
        """
        self.board = None
        self.port = port
        self.iterthread = None
        self.hiz_mode = hiz_mode
        self.analog_inputs = (0,1,2,3,4,5)
        self.pwm_outputs = (3,9,10,11)
        # keys: PWM pins, values: corresponding HI-Z control pins
        self.hiz_pins = {3:7, 9:8, 10:12, 11:13}
        self.sw_pins = (2,4,5,6)
        self._sw_state = None
        self.commands = {
            'vset': {'fun': self._vset},
            'vread': {'fun': self._vread},
            'sw_control': {'fun': self._sw_control}}
        self._vread_done = False

    def __del__(self):
        self.disconnect()

    def connect(self):
        """Connect to the board, attach custom SysEx handler, and do some inits.

        Starting conditions:
            All PWM outputs start at 0.0 volts.
            If HI-Z mode is enabled, all outputs will be at HI-Z.
        """
        try:
            board = None
            board = pyfirmata.Arduino(self.port)

            board.add_cmd_handler(REPORT_ANALOG_NOW_RESPONSE, self._handle_report_analog_now)
        except Exception as e:
            if board:
                board.exit()
            return False, str(e)
        else:
            # initializations to be sent to the board go here

            # switch control pins initializations
            for pin in self.sw_pins:
                board.digital[pin].mode = pyfirmata.OUTPUT
                # all outputs on HI-Z
                self._sw_control('hiz')
            # HI-Z pins init
            for pin in self.hiz_pins:
                board.digital[pin].mode = pyfirmata.OUTPUT
                # all outputs on HI-Z if the mode is enabled, and viceversa
                state = 1 if self.hiz_mode else 0
                board.digital[pin].write(state)
            # PWM pins to zero volts
            for i in self.pwm_outputs:
                board.digital[i].mode = pyfirmata.PWM
                board.digital[i].write(0.0)
            self.board = board
            return True, 'Serial object connection successful'

    def disconnect(self):
        """Reset the board, disconnect it and destroy the pyfirmata object,
        along the reporting thread if it's running.
        """
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

        Args:
            cmd (str): command name as specified in __init__()
            params (list): list of arguments for the command. Specified elsewhere.
        Returns:
            None or any value read, depending on the requested command.
        """
        if cmd not in self.commands:
            raise ValueError('Unexpected command: {}'.format(cmd))

        return self.commands[cmd]['fun'](*params)

    def sampling_interval(self, milis):
        """Set the reporting sampling interval on the board.

        Sampling is bounded to (10, 16383) ms.
        """
        # minimum sampling interval supported is 10ms
        if milis > 16383:
            milis = 16383
        self.board.send_sysex(pyfirmata.SAMPLING_INTERVAL,
                              bytearray([milis % 128, milis >> 7]))

    def _vset(self, pins, values, zero_is_hiz=False):
        """Quickly send PWM values to the board.

        Args:
            pins (int list): any combination of (3,9,10,11)
            values (float list): in the range 0..1, corresponding to the pins list
            zero_is_hiz (bool): whether to treat a zero value as HI-Z output. If `hiz_mode` is `True`, this arg has no effect
        """
        for pin, value in zip(pins, values):
            # get the HI-Z controller pin corresponding to the current PWM pin
            hizpin = self.hiz_pins[pin]
            # set digital pin controlling hf4066 IC switch accordingly
            if (zero_is_hiz or self.hiz_mode) and value == 0.0:
                self.board.digital[hizpin].write(1)
            else:
                self.board.digital[hizpin].write(0)
            self.board.digital[pin].write(value)

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
        """Handler for our custom SysEx message, to be registered in the
        pyFirmata object `self.board`.

        This method accesses the `value` attribute somewhere inside
        `self.board`, which is not too neat. However this avoids having to
        subclass or fork the library in order to implement this functionality.
        """
        for i in range(0, len(args), 3):
            pin, lsb, msb = args[i], args[i+1], args[i+2]
            value = round(float((msb << 7) + lsb) / 1023, 4)
            self.board.analog[pin].value = value
        self._vread_done = True

    def enable_reporting(self, sampling=1000):
        """Enable reporting of all the analog pins."""
        # start reader thread to catch reported values
        # the thread only stops when the serial connection is closed
        it = pyfirmata.util.Iterator(self.board)
        it.start()
        it.daemonic = True  # stop the thread if main program quits
        self.iterthread = it

        for pin in self.analog_inputs:
            self.board.analog[pin].enable_reporting()

        self.sampling_interval(sampling)

    def _vsweep(self, out_pins, in_pins, out_values, settling):
        """Perform a sweep of voltages.

        WARNING: It is quite blocking due to the settling waiting time and the
        possibly long loop.

        TODO: find a better implementation to avoid blocking the server.

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
            step = self._vread(in_pins)
            # append the steps together
            results.append(step)
        return results

    def _sw_control(self, cmd, duration=0.0):
        """Function controlling the switch actions.

        Switch control terminals (a,b,c,d) are assumed to be connected to the
        pins set in self.sw_pins. A and B are the outputs of the switches, with
        (a,b) connected to A, and (c,d) to B. Values of 0 are assumed to open
        the switch. Switches (a,b,c,d) inputs are assumed to be connected to
        (V+,0,V+,0).

        a b c d | A  B  cmd
        --------------------
        1 0 0 1 | V+ 0  a
        0 1 1 0 | 0  V+ b
        0 1 0 1 | 0  0  0
        1 0 1 0 | V+ V+ v+
        0 0 0 0 | Z  Z  z

        Additional commands (cmd):
            'flip': changes between 'a' and 'b'
            'pulse_a': sets state 'a' for `duration`, then sets 'hiz'
            'pulse_b': sets state 'b' for `duration`, then sets 'hiz'

        Args:
            cmd (str): selected command
            duration (float): pulse width in miliseconds
        """
        def write_pins(vals):
            for i, pin in enumerate(self.sw_pins):
                self.board.digital[pin].write(vals[i])

        if cmd == 'a':
            write_pins((1,0,0,1))
            self._sw_state = 'a'
        elif cmd == 'pulse_a':
            write_pins((1,0,0,1))
            time.sleep(duration)
            write_pins((0,0,0,0))
        elif cmd == 'b':
            write_pins((0,1,1,0))
            self._sw_state = 'b'
        elif cmd == 'pulse_b':
            write_pins((0,1,1,0))
            time.sleep(duration)
            write_pins((0,0,0,0))
        elif cmd == 'v+':
            write_pins((1,0,1,0))
        elif cmd == '0':
            write_pins((0,1,0,1))
        elif cmd == 'z':
            write_pins((0,0,0,0))
        elif cmd == 'flip':
            # change between 'a' and 'b', or goto 'a' otherwise
            if self._sw_state == 'a':
                self._sw_state = 'b'
                write_pins((0,1,1,0))
            else:
                self._sw_state = 'a'
                write_pins((1,0,0,1))
