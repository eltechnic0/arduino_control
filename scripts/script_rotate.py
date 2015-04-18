from modules.app_script import Script
import math

class AppScript(Script):
    def __init__(self, cherry):
        Script.__init__(self, cherry)
        self.data = []
        _ = self.serial_write('verbose', [0])   # disable verbosity

    def run(self, steps=10, radius, pins=(3,9,10,11)):
        """
        :pins   [right top left bottom]
        """
        for i in range(steps):
            valx = radius*math.cos(i*2*Math.pi/steps)
            valy = radius*math.sin(i*2*Math.pi/steps)
            values = [0 0 0 0]
            i = 0 if valx > 0 else 2
            j = 1 if valy > 0 else 3
            values[i] = int(abs(valx))
            values[j] = int(abs(valy))
            _ = self.serial_write('vset', [pins, values, settling])
            self.data.append(valx,valy)
            yield self.data
