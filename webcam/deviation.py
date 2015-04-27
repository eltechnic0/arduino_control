from skimage.segmentation import clear_border
from skimage.morphology import square, opening
# from skimage.feature import canny
from skimage.filters import threshold_otsu
from skimage.color import rgb2gray
from skimage.io import imread
from skimage.measure import regionprops
from scipy.ndimage import label
import matplotlib.pyplot as plt
import numpy as np
import json

class Deviation(object):
    """docstring for Deviation
    :self.rect is [(x1, y1), (x2, y2)] for topleft and bottomright respectively
    """
    def __init__(self, calibrationfile):
        # super(Deviation, self).__init__()
        self.load_calibration(calibrationfile)

    def load_image(self, filename):
        # self.image in numpy array format
        self.image = rgb2gray(imread(filename))

    # def set_calibration(self, calibration):
    #     self.rect = calibration

    def load_calibration(self, filename):
        with open(filename, 'r') as f:
            rect = json.load(f)
            self.rect = [(rect["topleft"]["x"], rect["topleft"]["y"]),
                        (rect["bottomright"]["x"], rect["bottomright"]["y"])]
            self.rect = [(int(x), int(y)) for x,y in self.rect]
            # self.rect = [(int(i["x"]), int(i["y"])) for i in rect.values()]

    def spot_coordinates(self):
        # check whether to include last element of the slice or not
        # note that self.rect has (0,0) at top left and that the np image array
        # is like [rows, cols], so we use y for rows, and x for cols
        rect = self.rect
        slc = self.image[rect[0][1]:rect[1][1], rect[0][0]:rect[1][0]]
        thresh = threshold_otsu(slc)
        binary = slc > thresh
        clear_border(binary)
        binary = opening(binary, square(2))
        labelim, _ = label(binary)
        regions = regionprops(labelim)

        plt.gray()
        fig, axes = plt.subplots(1, 3, figsize=(10,10))
        axes[0].imshow(slc)
        # axes[0].axis('off')
        axes[1].imshow(labelim)
        for i, reg in enumerate(regions):
            y, x = reg.centroid
            axes[1].plot(x,y,'.r')
            print('Coords for region {}: {}'.format(i, (round(x),round(y))))
        axes[2].imshow(self.image)

        plt.savefig('out.png', bbox_inches='tight')
        # import matplotlib.image as mpimg
        # mpimg.imsave("out.png", img)
        return regions

if __name__ == '__main__':
    dev = Deviation('../public/cam_calibration.json')
    dev.load_image('../public/outfile.jpeg')
    regs = dev.spot_coordinates()
    print(regs)
