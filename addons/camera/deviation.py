import json
import matplotlib.pyplot as plt
import numpy as np
import platform
from scipy.ndimage import label
from skimage.io import imread
from skimage.measure import regionprops
from skimage.morphology import disk as mdisk
from skimage.morphology import binary_opening
from subprocess import call


class Deviation(object):
    """The class should be used like this:
    1- Instantiate with a calibration file, which shouldn't change for the whole
        experiment
    2- Capture the image from the camera - capture(filename, device)
    3- Get the spot coords and optionally plot result - findspot(figpath)
    Repeat 2-3 as needed.

    `self.rect` is [(x1, y1), (x2, y2)] for topleft and bottomright respectively.
    """
    def __init__(self, calibrationfile):
        # the plotting backend switch is usually required
        self.load_calibration(calibrationfile)
        print('Plotting backend:', plt.get_backend())
        print('Switching to Agg...')
        plt.switch_backend('Agg')
        print('Plotting backend:', plt.get_backend())

    def load_image(self, filename):
        """Load an image file.
        """
        self.image = imread(filename)

    def load_calibration(self, filename):
        """Load a calibration file.
        """
        with open(filename, 'r') as f:
            rect = json.load(f)
            self.rect = [(rect["topleft"]["x"], rect["topleft"]["y"]),
                         (rect["bottomright"]["x"], rect["bottomright"]["y"])]
            self.rect = [(int(x), int(y)) for x, y in self.rect]

    def findspot(self, figpath=None, spotsize=15):
        """Find the coordinates of the laser spot based on choosing a bin of the
        image histogram with an amount of bright pixels lower than `spotsize`.

        Args:
            figpath (str): specifies the path for the plot, or no plot if not given.
            spotsize (int): is the number of pixels considered sufficient to be a spot.

        Returns:
            found coordinates as (coordx, coordy)
        """
        rect = self.rect
        # working only on the red channel
        impart = self.image[rect[0][1]:rect[1][1]+1, rect[0][0]:rect[1][0]+1, 0]
        hvals, bins = np.histogram(impart, bins=20)
        # adaptive threshold finding depending on the minimum spot size
        index = 19
        while index > 10:
            # search for minimum number of bright pixels
            if sum(hvals[index:]) > spotsize:
                break
            else:
                index -= 1
        binary = impart >= bins[index]
        labelim, _ = label(binary)
        regions = regionprops(labelim)
        if len(regions) > 1:
            binary = binary_opening(binary, mdisk(1))
            labelim, _ = label(binary)
            regions = regionprops(labelim)
            if len(regions) == 0:
                return None
        # plotting if there is a save path for the figure
        if figpath:
            plt.gray()
            fig, ax = plt.subplots(1, 1, figsize=(5, 5))
            height, width = labelim.shape
            # bound axes to the grid ref sys
            ax.set_xlim(-100, 100)
            ax.set_ylim(-100, 100)
            # all transparent black pixels
            rgbalabelim = np.zeros((labelim.shape[0], labelim.shape[1], 4))
            # opaque on white pixels
            rgbalabelim[binary, 3] = 1
            # blue on white pixels
            rgbalabelim[binary, 2] = 1
            # scale and position image on the right spot
            ax.imshow(impart, extent=[-100, 100, -100, 100], origin='upper')
            # plot white pixels as blue and leave the rest untouched
            ax.imshow(rgbalabelim,
                      extent=[-100, 100, -100, 100], origin='upper')
            ax.plot(0, 0, '+', color='lime', markersize=10, markeredgewidth=1.5)
            # scale centroid to extents
            # TODO: check if its 200 or 201
            sx, sy = 200/width, 200/height
            for i, reg in enumerate(regions):
                # conversion to the coordinates of the grid - center at (0,0)
                y, x = reg.centroid
                x, y = x - width/2, -y + height/2
                ax.plot(sx*x, sy*y, '+r', markersize=10, markeredgewidth=1)
                if i >= 19:
                    break
            fig.savefig(figpath, bbox_inches='tight')
        # still plot, but notify it didn't work
        if len(regions) > 1:
            return None
        return x, y

    def capture(self, filename, device):
        """Capture and save a snapshot from a webcam, then load it.

        CommandCam.exe most useful options:
            /devname    select device by name as seen with /devlist
            /devnum     select device by number
            /devlist    list devices
            /filename   captured image destination file

        Args:
            device (str): name of the capture device. Example: Linux '/dev/video0'.
            filename (str): is the destination path for the snapshot image.
                Extension must be included and be in jpeg format.
        """
        plat = platform.system()
        if plat == 'Windows':
            # TODO: check if it works
            args = 'CommandCam.exe /devname {} /filename {}'.format(device, filename).split()
        else:
            args = 'streamer -c {} -o {}'.format(device, filename).split()
        _ = call(args)
        self.load_image(filename)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-O", dest='outfig', action='store_false', default=True,
                        help='disable figure output')
    args = parser.parse_args()
    dev = Deviation('static/calibration.json')
    dev.load_image('static/outfile.jpeg')
    if args.outfig:
        dev.findspot('static/processed.png')
    else:
        dev.findspot()
