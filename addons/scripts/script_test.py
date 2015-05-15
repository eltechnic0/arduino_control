from modules.app_script import Script


class AppScript(Script):
    def __init__(self, cherry):
        Script.__init__(self, cherry)

    def run(self, string=None, array=None):
        result = self.serial_write('comtest')
        self.cherrypy.engine.log('Arduino response: ' + str(result))
        self.cherrypy.engine.log('Received string: ' + string)
        self.cherrypy.engine.log('Received array: ' + str(array))
        return result
