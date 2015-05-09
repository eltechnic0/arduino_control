import json
import os
import math

import cherrypy
from addons.cam_calibration.deviation import Deviation


class AppAddon(object):
    def __init__(self,
                 html_file='index.html',
                 image_file='outfile.jpeg',
                 calib_file='calibration.json',
                 proc_file='processed.png',
                 addon_path='addons/camera'):
        """
        :url is the mount point
        :text is the displayed text
        """
        self.addon_conf = {
            'url': '/camera',
            'text': 'Camera control'
        }
        ppath = os.path.join(addon_path, 'static')
        self.cpconf = {
            '/': {
                'tools.staticdir.root': os.path.abspath(os.getcwd())
            },
            '/static': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': ppath
            }
        }
        self.html_file = os.path.join(ppath, html_file)
        self.image_file = os.path.join(ppath, image_file)
        self.calib_file = os.path.join(ppath, calib_file)
        self.proc_file = os.path.join(ppath, proc_file)
        self.static_path = ppath
        try:
            self.deviation = Deviation(os.path.join(ppath, calib_file))
        except Exception as e:
            cherrypy.engine.log('ERROR '+str(e))

    @cherrypy.expose
    def index(self):
        return open(self.html_file)

    @cherrypy.expose
    def capture(self, device):
        try:
            self.deviation.capture(self.image_file, device)
        except Exception as e:
            return {'success': False, 'info': str(e), 'data': None}
        return {'success': True}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def save_calibration(self):
        rect = cherrypy.request.json
        try:
            with open(self.calib_file, 'w') as f:
                json.dump(rect, f)
        except Exception as e:
            cherrypy.engine.log('ERROR ' + str(e))
            return {'success': False}
        else:
            try:
                self.deviation.load_calibration(self.calib_file)
            except Exception as e:
                cherrypy.engine.log('ERROR '+str(e))
        return {'success': True}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def process(self, spotsize=15):
        return self.findspot(int(spotsize))

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def capture_and_process(self, device, spotsize=15):
        try:
            self.deviation.capture(self.image_file, device)
        except Exception as e:
            return {'success': False, 'info': str(e), 'data': None}
        return self.findspot(int(spotsize))

    def findspot(self, spotsize):
        coords = self.deviation.findspot(self.proc_file, spotsize)
        if coords:
            data = '({:.4},{:.4})'.format(*coords)
            return {'success': True, 'info': 'OK', 'data': data}
        else:
            return {'success': False, 'info': 'Spot not found', 'data': None}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def characterize(self, device, spotsize=15, steps=10, radii=None,
                     pins=(3, 9, 10, 11), settling=250):
        """
        Returns data as a list of (radius,xgrid,ygrid,xcoord,ycoord,isok).

        The function assumes that the calibration is already loaded.

        Coordinates that could not be recognized have a value of None. Those
        that were not recognized with the requested `spotsize` have a value
        `isok` False.

        :steps  number of divisions of 360º
        :radii sequence of numbers between 0 and 255
        :pins   (right top left bottom)
        """
        dev = self.deviation
        data = []
        for radius in radii:
            for k in range(steps):
                valx = radius*math.cos(k*2*math.pi/steps)
                valy = radius*math.sin(k*2*math.pi/steps)
                values = [0, 0, 0, 0]
                i = 0 if valx > 0 else 2
                j = 1 if valy > 0 else 3
                values[i] = int(abs(valx))
                values[j] = int(abs(valy))
                res = cherrypy.engine.publish('serial-write',
                                              ['vset', pins, values, settling])
                if not res['success']:
                    # data.append((radius,valx,valy,None,None,False))
                    # continue
                    return res
                # capture image and find the spot coordinates without plotting
                dev.capture(self.image_file, device)
                coords = dev.findspot(None, spotsize)
                # another try with 50% bigger spotsize
                if not coords:
                    coords = dev.findspot(None, round(1.5*spotsize))
                    if not coords:
                        data.append((radius, valx, valy, None, None, False))
                    else:
                        data.append((radius, valx, valy,
                                    coords[0], coords[1], False))
                    continue
                data.append((radius, valx, valy, coords[0], coords[1], True))
        return {'success': True, 'data': data, 'info': 'Characterization'}
