#!/usr/bin/python

import spear.LPR.charRecog
import os
import sys

prog_path = os.path.dirname(os.path.realpath(__file__))

template_letter_path = prog_path + "/spear/template/demo_letter/"
template_number_path = prog_path + "/spear/template/demo_number/"

letter_reader = spear.LPR.charRecog.CharReader(template_letter_path)
number_reader = spear.LPR.charRecog.CharReader(template_number_path)

test_img_path = str(sys.argv[1])
test_img = spear.SimpleCV.Image(test_img_path)

if len(sys.argv) == 2:
    letter_reader.findMatch(test_img, perform_unit_test=True)
elif len(sys.argv) == 3:
    number_reader.findMatch(test_img, perform_unit_test=True)

