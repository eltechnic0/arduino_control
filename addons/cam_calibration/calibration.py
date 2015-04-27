import json
import cherrypy
from subprocess import call
import os

class AppAddon(object):
    def __init__(self,
                html_file='cam_calibration.html',
                image_file='outfile.jpeg',
                calib_file='cam_calibration.json',
                addon_path='addons/cam_calibration'):
        """
        :url is the mount point
        :text is the displayed text
        """
        self.addon_conf = {
            'url': '/calibration',
            'text': 'Camera calibration'
        }
        public_path = os.path.join(addon_path, 'public')
        self.cpconf = {
            '/': {
                'tools.staticdir.root': os.path.abspath(os.getcwd())
            },
            '/static': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': public_path
            }
        }
        self.html_file = os.path.join(public_path, html_file)
        self.image_file = os.path.join(public_path, image_file)
        self.calib_file = os.path.join(public_path, calib_file)

    @cherrypy.expose
    def index(self):
        return open(self.html_file)

    @cherrypy.expose
    def refresh(self):
        args = 'streamer -c /dev/video0 -o {}'.format(self.image_file).split()
        try:
            res = call(args)
        except Exception as e:
            cherrypy.engine.log('ERROR '+str(e))
        return

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def save(self):
        rect = cherrypy.request.json
        try:
            with open(self.calib_file,'w') as f:
                json.dump(rect, f)
        except Exception as e:
            cherrypy.engine.log('ERROR ' + str(e))
            return False
        return True
