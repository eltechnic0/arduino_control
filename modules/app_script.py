class Script(object):
    """
    Base scripting class that must be sublcassed by any custom script
    """
    def __init__(self, cherry):
        self.cherrypy = cherry
        self.data = None

    def run(self, **kwargs):
        """
        The code to run must be inside this function.
        """
        raise NotImplementedError('This function must be overriden')

    def serial_write(self, cmd, params=[]):
        """
        Convenience function to write to the serial device. It uses the
        `SerialObjectPlugin`.
        """
        return self.cherrypy.engine.publish('serial-write', [cmd] + params)[0]
