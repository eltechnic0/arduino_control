from modules.app_script import Script

class AppScript(Script):
    def __init(self, cherry):
        Script.__init__(self, cherry)

    def run(self, string=None):
        result = self.serial_write('comtest')
        self.cherrypy.engine.log(str(result))
        self.cherrypy.engine.log('Received string: '+string)
        return result
