#!/usr/bin/python
import SimpleCV
import spear.plateRecog
import sys
import time

inp_img_path = str(sys.argv[1])
inp_img = SimpleCV.Image(inp_img_path)

speedtest = False
if len(sys.argv) == 3 and sys.argv[2] == '--speed':
    speedtest = True
    debug = False
elif len(sys.argv) == 3:
    debug = True
else:
    debug = False

if speedtest:
    print "Performing speed test"
    time_now = time.time()
    spear.plateRecog.scanImage(inp_img, debug=debug)
    time_then = time.time()
    print "Processing time: %f" %(time_then - time_now)
else:
    spear.plateRecog.scanImage(inp_img, debug=debug)

