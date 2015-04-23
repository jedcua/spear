#!/usr/bin/python

import sys, SimpleCV, spear.LPR.charLocate, spear.LPR.rgbParser

imagePath = str(sys.argv[1])

if len(sys.argv) == 3:

    img = SimpleCV.Image(imagePath)
    isInt = True

    try:
        thresh = int(sys.argv[2])
    except TypeError:
        isInt = False

    if isInt:
        thresh = int(sys.argv[2])
        mask = img.threshold(thresh)

    else:
        rgbPath = str(sys.argv[2])

        rgbData = spear.LPR.rgbParser.rgbData(rgbPath)

        r1, g1, b1 = rgbData.getMinRange()
        r2, g2, b2 = rgbData.getMaxRange()

        r1, g1, b1 = int(r1), int(g1), int(b1)
        r2, g2, b2 = int(r2), int(g2), int(b2)

        mask = img.createBinaryMask((r1, g1, b1), (r2, g2, b2)).morphClose()

else:
    mask = SimpleCV.Image(imagePath)

spear.LPR.charLocate.findChar(mask,
                              perform_unit_test=True,
                              right_click_save=True,
                              guess_missing=False,
                              CENTER_POS=0.50)
