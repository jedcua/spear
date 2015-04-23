"""
RGB Parser Module. by Jed

Usage:
    rgbData("fileTo/rgbFile")
    rgbData.getMinRange()
    rgbData.getMaxRange()
"""

class  rgbData:

    def __init__(self,filePath):

        #Define 3 List for RGB
        self.rList = []
        self.gList = []
        self.bList = []

        #Load rgb file
        self.rgbFile = open(filePath,'r')

        for line in self.rgbFile:
            self.rgb = line.strip('\n').strip('(').strip(')').split(',')
            self.r = float(self.rgb[0].strip())
            self.g = float(self.rgb[1].strip())
            self.b = float(self.rgb[2].strip())

            #Append rgb to list
            self.rList.append(self.r)
            self.gList.append(self.g)
            self.bList.append(self.b)

        #Sort the lists
        self.rList = sorted(self.rList)
        self.gList = sorted(self.gList)
        self.bList = sorted(self.bList)

    def getMinRange(self):

        return (self.rList[0],self.gList[0],self.bList[0])

    def getMaxRange(self):

        return (self.rList[-1],self.gList[-1],self.bList[-1])


