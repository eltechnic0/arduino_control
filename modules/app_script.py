class Script(object):
    def __init__(self, cherry):
        self.cherrypy = cherry
        self.data = None

    def run(self, **kwargs):
        raise NotImplementedError('This function must be overriden')

    def serial_write(self, cmd, params=[]):
        return self.cherrypy.engine.publish('serial-write', [cmd] + params)[0]
