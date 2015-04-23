#!/usr/bin/python

import spear.LPR.imageProcessing
import spear.LPR.maskCreate
import sys
import time

imagePath = str(sys.argv[1])

img = spear.SimpleCV.Image(imagePath)

img = spear.LPR.imageProcessing.equalize(img)

img = spear.LPR.imageProcessing.denoiseBilateralFilter(img)

img.show()
time.sleep(2)

spear.LPR.maskCreate.colorSegmentation(img, perform_unit_test=True, right_click_save=True)

