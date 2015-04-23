import SimpleCV
import os
import numpy

prog_path = os.path.dirname(os.path.realpath(__file__))
stencil_dir_path = prog_path + "/stencil/"
stencil_images = SimpleCV.ImageSet(stencil_dir_path)


class Stencil(object):

    def __init__(self, blobs, mask):
        self.blobs = blobs
        self.mask = mask

'''
class FakeBlob(object):

    def __init__(self, bound_box):
        x, y, w, h = bound_box

        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def minX(self):
        return self.x

    def maxX(self):
        return self.x + self.w

    def minY(self):
        return self.y

    def maxY(self):
        return self.y + self.h

    def width(self):
        return self.w

    def height(self):
        return self.h
'''

class FakeBlob(object):

    def __init__(self, top_left, bottom_right): #, input_image):
        x1, y1 = top_left
        x2, y2 = bottom_right

        #cropped_img = input_image[x1:x2, y1:y2]

        self.x = (x1 + x2) / 2
        self.y = ((y1 + y2) / 2)
        #self._baseImage = input_image

        self.width = lambda : x2-x1
        self.height = lambda : y2-y1
        self.minX = lambda : x1
        self.maxX = lambda : x2
        self.minY = lambda : y1
        self.maxY = lambda : y2
        #self.blobImage = lambda : cropped_img
        #self.blobMask = lambda : cropped_img.binarize().invert()


def guessMissingBlobs(input_blobs, input_image, debug):

    if len(input_blobs) < 4:
        print "Insuficient number of blobs! Cannot guess"
        return None

    if len(input_blobs) >= 6:
        print "Already have required number of blobs."
        return input_blobs

    test_stencil = _createStencilMask(input_blobs, input_image, debug)

    #Get best match for each stencil
    template_match_list = []
    for template_stencil in stencil_images:
        guess_stencil_mask, best_match_value = _slideStencils(test_stencil, template_stencil, debug)
        print 'Stencil Match: %s:%i' %(template_stencil.filename, best_match_value)
        template_match_list.append((guess_stencil_mask, best_match_value))

    #Get best match amoung stencils
    best_stencil, __ = sorted(template_match_list, key=lambda stencil: stencil[1])[0]

    final_blobs =  _getMissingBlobsFromStencil(input_blobs, test_stencil, best_stencil, debug)
    return final_blobs


def _createStencilMask(input_blobs, input_image, debug):
    """
    Method:
        Create a Black Image with same dimensions are input_image, and
        draw White Rectangles corresponding to locations and dimensions
        of input_blobs

    Parameters:
        input_blobs - List of SimpleCV.Blob.
        input_image - Need for specifying dimensions.
        debug       - Show detailed visual output.

    Returns:
        SimpleCV.Image, Black image with several White Rectangles
    """

    img_w, img_h = input_image.width, input_image.height

    test_img = SimpleCV.Image((img_w, img_h))

    for blob in input_blobs:
        x, y, w, h = blob.boundingBox()

        test_img.dl().rectangle((x, 0), (w, img_h), color=(255, 255, 255),
                                 width=1, filled=True)

    test_img = test_img.applyLayers()

    if debug:
        test_img.live()

    return test_img


def _slideStencils(test_stencil, template_stencil, debug):

    test_mask = test_stencil
    template_mask = template_stencil

    test_blobs = sorted(test_mask.findBlobs(), key=lambda blob: blob.x)
    template_blobs = sorted(template_mask.findBlobs(), key=lambda blob: blob.x)

    #Make sure test_mask is scaled to match height with template_mask
    correction_factor = float(test_blobs[0].width()) / template_blobs[0].width()
    template_mask = template_mask.scale(correction_factor)
    template_blobs = sorted(template_mask.findBlobs(), key=lambda blob: blob.x)

    start = test_blobs[0].minX() - (template_blobs[-1].maxX() - template_blobs[0].minX())
    end = test_blobs[-1].maxX()
    offset = template_blobs[0].minX()

    holder_img = SimpleCV.Image((test_mask.width, test_mask.height+template_mask.height))

    #Get best x location with best match
    similarness = []
    for x in xrange(start, end):

        slide_template_img = SimpleCV.Image((test_mask.width, template_mask.height)).blit(template_mask, (x-offset, 0))

        if debug:
            holder_img.blit(test_mask, (0, 0)).blit(slide_template_img, (0, test_mask.height)).show()

        similarity_score = _getSimilarity(test_mask, slide_template_img, debug)
        similarness.append((similarity_score, x))

    #Create stencil based on best match
    similarness = sorted(similarness, key=lambda tup: tup[0], reverse=False)
    peak_value, x = similarness[0]

    guess_stencil_mask = SimpleCV.Image((test_mask.width, test_mask.height)).blit(template_mask, (x-offset, 0))

    if debug:
        holder_img.blit(test_mask, (0, 0)).blit(guess_stencil_mask, (0, test_mask.height)).live()

    return (guess_stencil_mask, peak_value)


def _getSimilarity(image1, image2, debug):

    image1_line = image1.getHorzScanlineGray(0)
    image2_line = image2.getHorzScanlineGray(0)

    if len(image1_line) != len(image2_line):
        print "Warning! Have different width!"
        return None

    similarity_score = numpy.absolute(image1_line - image2_line).sum()

    if debug:
        print similarity_score

    return similarity_score


def _getMissingBlobsFromStencil(given_blobs, test_stencil, template_stencil, debug):

    if test_stencil.width != template_stencil.width:
        print "Error! Test and Template Stencil have different width!"
        return None

    #Only provide blobs that are missing, dont alter known blobs
    template_blobs = sorted(template_stencil.findBlobs(), key=lambda blob: blob.x)
    template_map = [None] * len(template_blobs)

    for index, template_blob in enumerate(template_blobs):
        for given_blob in given_blobs:
            #Check if two blobs overlap
            diff_minX = _isClose(template_blob.minX(), given_blob.minX())
            diff_maxX = _isClose(template_blob.maxX(), given_blob.maxX())

            if diff_minX and diff_maxX:
                template_map[index] = given_blob
                break

    #Those with None are missing, provide them with a blob!a
    new_blobs = template_map[:]
    for index, map_element in enumerate(template_map):
        if map_element is None:
            blob = template_blob[index]
            top_left = blob.minX(), blob.minY()
            bottom_right = blob.maxX(), blob.maxY()
            new_blobs[index] = FakeBlob(top_left, bottom_right)

    if debug:

        debug_img = SimpleCV.Image((test_stencil.width, test_stencil.height))

        for blob in new_blobs:
            color = (0, 255, 0)

            if isinstance(blob, FakeBlob):
                color = (0, 0, 255)

            debug_img.dl().rectangle2pts((blob.minX(), 0), (blob.maxX(), test_stencil.height),
                                         width=0, color=color, filled=True)
            debug_img = debug_img.applyLayers()

        debug_img.live()

    return new_blobs


def _isClose(val1, val2, TOLERANCE=0.02):

    diff = float(abs(val1-val2)) / (val1+val2)
    if diff <= TOLERANCE:
        return True
    else:
        return False

