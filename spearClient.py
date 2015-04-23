#!/usr/bin/python
"""
Usage:
    ./testHud.py [(HOST PORT) --dummy=IMAGE]

Options:
    --dummy=<image>  Use an image as dummy camera source.
"""

import spear.hud
import os
import docopt

arguments = docopt.docopt(__doc__)
print arguments

progPath = os.path.dirname(os.path.realpath(__file__))

hudImgPath = progPath + "/HUD/hudb.png"
maskImgPath = progPath + "/HUD/mask.png"
scanHudImgPath = progPath + "/HUD/standby.png"
testPath = progPath + "/testResult"

#Parse Arguments
dummyImagePath = arguments.get("--dummy")
host = arguments.get("HOST")
port = arguments.get("PORT")
if port is not None:
    port = int(port)

hud = spear.hud.SpearHUD(hudImgPath, maskImgPath, scanHudImgPath,
                         serverHost=host, serverPort=port,
                         savePath=testPath, dummyImagePath=dummyImagePath)

hud.run() #Blocking call
