#!/usr/bin/python

import spear.LPR.plateLocate, sys
import spear.LPR.imageProcessing

input_image_path = str(sys.argv[1])

img = spear.SimpleCV.Image(input_image_path)

cropped_img = spear.LPR.imageProcessing.cropToROI(img)
eq_img = spear.LPR.imageProcessing.equalize(cropped_img)

rect_obj_list = spear.LPR.plateLocate.findPlate(eq_img, perform_unit_test=True, right_click_save=True)

