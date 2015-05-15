from modules.app_script import Script
import time


class AppScript(Script):
    def __init__(self, cherry):
        Script.__init__(self, cherry)
        self.data = []

    def run(self, out_pins, in_pins, out_values, settling):
        """Performs a sweep of voltages.

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
            res = self.serial_write('vset', (out_pins, vals))
            # wait for settling time after all pins are written
            time.sleep(settling/1000)
            # collect the readings of the current step
            step = self.serial_write('vread', (in_pins,))
            # append the steps together
            results.append(step)
        return results
