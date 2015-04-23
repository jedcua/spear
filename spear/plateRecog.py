import LPR.maskCreate
import LPR.charLocate
import LPR.imageProcessing
import LPR.charGuess
import LPR.charRecog
import os
import matplotlib.pyplot as plt
import numpy


#Initialize CharReader object for Character Recognition
prog_path = os.path.dirname(os.path.realpath(__file__))

template_letter_path = prog_path + "/LPR/template/all_letter/"
template_number_path = prog_path + "/LPR/template/all_number/"
all_path = prog_path + "/LPR/template/all/"

letter_reader = LPR.charRecog.CharReader(template_letter_path)
number_reader = LPR.charRecog.CharReader(template_number_path)
all_reader = LPR.charRecog.CharReader(all_path)


def scanImage(input_image, debug=False):

    #IMAGE ENCHANCEMENT
    processed_image = _preProcessRawImage(input_image, debug)

    #UNCROPPED THRESHOLD SWEEP
    char_blobs_uncropped_threshold_sweep = _exhaustiveThresholdSweep(processed_image, debug)
    if char_blobs_uncropped_threshold_sweep is None: return None

    #IMAGE CROP AND COLOR ANALYSIS
    cropped_region, (yLower, yUpper) = _smartCrop(char_blobs_uncropped_threshold_sweep, processed_image, debug)
    ave_color, min_color, max_color = _getAveMinMaxColors(char_blobs_uncropped_threshold_sweep, processed_image, debug)

    #CROPPED THRESHOLD SWEEP
    char_blobs_cropped_threshold_sweep = _exhaustiveThresholdSweep(cropped_region, debug)
    if char_blobs_cropped_threshold_sweep is None: char_blobs_cropped_threshold_sweep = []

    #COLOR SWEEP
    char_blobs_color_sweep = _adaptiveColorSweep(cropped_region, ave_color, min_color, max_color, debug)
    if char_blobs_color_sweep is None: char_blobs_color_sweep = []

    #DETERMINE BEST BLOB TO USE
    blobs_and_methods = [(char_blobs_color_sweep, cropped_region, 'Color Sweep'),
                         (char_blobs_cropped_threshold_sweep, cropped_region, 'Cropped Threshold Sweep'),
                         (char_blobs_uncropped_threshold_sweep, processed_image, 'Uncropped Threshold Sweep')]

    char_blobs_to_use, image_to_use, used_method = _determineBestMethod(blobs_and_methods, debug)

    #BINARIZE AND READ CHARACTER BLOBS
    otsu_mask_list = _cropAndOtsuBinarize(char_blobs_to_use, image_to_use, debug)
    char_val_list = _readCharBlobs(otsu_mask_list, inp_type='Image', use_char_format=True, perform_unit_test=debug)
    print char_val_list

    #USED FOR HUD FEEDBACK
    rect_list = _markCharFoundWithRectangles(input_image, char_blobs_to_use, yLower, used_method)

    #RETURN VALUE
    if char_val_list:
        return char_val_list, rect_list
    else:
        return None


def _exhaustiveThresholdSweep(input_image, debug=False):

    mask_gen = LPR.maskCreate.thresholdSweep(input_image)

    best_count = 0
    best_found = None

    for mask in mask_gen:
        current_found = LPR.charLocate.findChar(mask, perform_unit_test=debug)

        if current_found:
            current_count = len(current_found[0])
        else:
            current_count = 0

        print "Found: %i" %current_count

        if current_count >= best_count:
            best_count = current_count
            best_found = current_found

    if best_found:
        print "Exhaustive Threshold Sweep: Best found, %i characters" %best_count
        return best_found[0]
    else:
        print "Exhaustive Threshold Sweep: Unable to find Character blobs."
        return None


def _otsuTranslationSweep(input_image, debug=False):

    max_height = input_image.height

    for h in xrange(200, max_height, 5):
        for y in xrange(0, max_height, 5):

            if y+h+10 > max_height:
                break

            cropped = input_image[0:-1, y:y+h]
            mask = cropped.binarize()

            found = LPR.charLocate.findChar(mask, perform_unit_test=debug)

            if found:
                return (found[0], cropped)

    print "Otsu Binarization: None Found."
    return None


def _getAveMinMaxColors(input_blobs, input_image, debug):

    r_total_list, g_total_list, b_total_list = [], [], []

    for char_blob in input_blobs:
        x1, y1 = char_blob.minX(), char_blob.minY()
        x2, y2 = char_blob.maxX(), char_blob.maxY()

        char_region = input_image[x1:x2, y1:y2]
        char_region = char_region.applyBinaryMask(char_region.binarize())

        r_list, g_list, b_list = _collectColorFromMask(char_region, char_blob.blobImage())

        if False:
            char_region.scale(5.0).live()

            plt.subplot(311)
            plt.hist(r_list, 50, facecolor='r')

            plt.subplot(312)
            plt.hist(g_list, 50, facecolor='g')

            plt.subplot(313)
            plt.hist(b_list, 50, facecolor='b')

            plt.show()

        r_total_list.extend(r_list)
        g_total_list.extend(g_list)
        b_total_list.extend(b_list)

    r_numpy = numpy.array(r_total_list)
    g_numpy = numpy.array(g_total_list)
    b_numpy = numpy.array(b_total_list)

    ave_color = (r_numpy.mean(), g_numpy.mean(), b_numpy.mean())
    min_color = (r_numpy.min(), g_numpy.min(), b_numpy.min())
    max_color = (r_numpy.max(), g_numpy.max(), b_numpy.max())

    if debug:
        print ave_color
        print min_color
        print max_color

        plt.subplot(311)
        plt.hist(r_list, 50, facecolor='r')

        plt.subplot(312)
        plt.hist(g_list, 50, facecolor='g')

        plt.subplot(313)
        plt.hist(b_list, 50, facecolor='b')

        plt.show()

    return (ave_color, min_color, max_color)


def _scaleXrange(start, stop, num_of_steps):

    constant = False
    reverse = False

    if start < stop:
        reverse = False
    elif start > stop:
        reverse = True
    else:
        constant = True

    val = float(start)
    step = float(abs(stop - start)) / num_of_steps
    current_step = 0

    if constant:
        while current_step < num_of_steps:
            yield int(val)

    if not reverse:
        while val < stop:
            yield int(val)

            val = _limitAdd(val, step)

            current_step += 1
            if current_step == num_of_steps:
                break

    elif reverse:
        while val > stop:
            yield int(val)

            val = _limitAdd(val, -step)

            current_step += 1
            if current_step == num_of_steps:
                break


def _collectColorFromMask(colored_image, mask_image):

    r_list, g_list, b_list = [], [], []

    for x in xrange(mask_image.width):
        for y in xrange(mask_image.height):

            if all(mask_image.getPixel(x, y)) > 0:
                r, g, b = colored_image.getPixel(x, y)

                r_list.append(r)
                g_list.append(g)
                b_list.append(b)

    return r_list, g_list, b_list


def _smartCrop(input_blobs, input_image, debug, top_padding=0, bottom_padding=20):

    yLower = min(input_blobs, key=lambda blob: blob.minY()).minY()
    yUpper = max(input_blobs, key=lambda blob: blob.maxY()).maxY()

    cropped_region = input_image[0:-1, (yLower-top_padding):(yUpper+bottom_padding)]
    cropped_region = LPR.imageProcessing.denoiseBilateralFilter(cropped_region)
    cropped_region = LPR.imageProcessing.adaptiveEqualize(cropped_region)

    if debug:
        cropped_region.live()

    return cropped_region, (yLower, yUpper)


def _limitAdd(val1, val2):

    result = val1 + val2
    if result < 0:
        result = 0
    elif result > 255:
        result = 255

    return result


def _adaptiveColorSweep(input_image, ave_rgb, min_rgb, max_rgb, debug):

    #Create generators for RGB Sweeping
    distances = [int(ave_rgb[0] - min_rgb[0]),
                       int(ave_rgb[1] - min_rgb[1]),
                       int(ave_rgb[2] - min_rgb[2]),
                       int(max_rgb[0] - ave_rgb[0]),
                       int(max_rgb[1] - ave_rgb[1]),
                       int(max_rgb[2] - ave_rgb[2])]

    max_step = max(distances)

    r_u = _scaleXrange(ave_rgb[0], max_rgb[0], max_step)
    g_u = _scaleXrange(ave_rgb[1], max_rgb[1], max_step)
    b_u = _scaleXrange(ave_rgb[2], max_rgb[2], max_step)
    r_l = _scaleXrange(ave_rgb[0], min_rgb[0], max_step)
    g_l = _scaleXrange(ave_rgb[1], min_rgb[1], max_step)
    b_l = _scaleXrange(ave_rgb[2], min_rgb[2], max_step)

    current_found = None
    best_found = None
    best_count = 0

    for r1, g1, b1, r2, g2, b2 in zip(r_l, g_l, b_l, r_u, g_u, b_u):

        min_color = r1, g1, b1
        max_color = r2+1, g2+1, b2+1
        print min_color, max_color, best_count

        char_mask = input_image.createBinaryMask(min_color, max_color)
        current_found = LPR.charLocate.findChar(char_mask, perform_unit_test=debug)

        if current_found:
            current_count = len(current_found[0])
        else:
            current_count = 0

        if current_count >= best_count:
            best_count = current_count
            best_found = current_found

    if best_found:
        print "Adaptive Color Sweep: Best found, %i characters" %best_count
        return best_found[0]
    else:
        print "Adaptive Color Sweep: Unable to find Character blobs."
        return None


def _determineBestMethod(blob_method_list, debug):

    if True:
        print "---------------------------------------------------"
        for blobs, __, method in blob_method_list:
            print "Method: %s -> %i Characters" %(method, len(blobs))
        print "---------------------------------------------------"

    methods = sorted(blob_method_list, key=lambda m: len(m[0]), reverse=True)[0]
    best_blob = methods[0]
    best_image = methods[1]
    best_method = methods[2]

    print "Using %s : %i characters" %(best_method, len(best_blob))
    return best_blob, best_image, best_method


def _preProcessRawImage(inp_img, debug=False):

    cropped_img = LPR.imageProcessing.cropToROI(inp_img)
    eq_img = LPR.imageProcessing.adaptiveEqualize(cropped_img, 5.0, (16, 16))

    if debug:
        eq_img.live()

    return eq_img


def _maskSynthesis(inp_img_region, use_rgb_mask, MIN_ALLOWED_BLOBS, debug):

    valid_mask_list = []

    raw_mask_list = LPR.maskCreate.thresholdSweep(inp_img_region, use_rgb_mask=use_rgb_mask)

    #Retain valid masks by performing Character Localization to each
    for this_mask in raw_mask_list:
        found_blobs = LPR.charLocate.findChar(this_mask,
                                              perform_unit_test=debug)

        #Valid Masks will not return None
        if found_blobs:
            if len(found_blobs[0]) >= MIN_ALLOWED_BLOBS:
                valid_mask_list.append(this_mask)

    #Construct a new Mask based on all accepted masks
    if len(valid_mask_list):
        combined_mask = reduce(lambda img1,img2 : (img1+img2), valid_mask_list)
        return LPR.charLocate.findChar(combined_mask, perform_unit_test=debug)

    else:
        return None


def _cropAndOtsuBinarize(input_blobs, input_image, debug):

    otsu_mask_list = []
    char_region_list = []
    for char_blob in input_blobs:
        x1, y1 = char_blob.minX(), char_blob.minY()
        x2, y2 = char_blob.maxX(), char_blob.maxY()

        char_region = input_image[x1:x2, y1:y2]
        otsu_char = char_region.binarize()

        char_region_list.append(char_region)
        otsu_mask_list.append(otsu_char)

    if debug:
        reduce(lambda a,b: a.sideBySide(b), char_region_list).live()
        reduce(lambda a,b: a.sideBySide(b), otsu_mask_list).live()

    return otsu_mask_list


def _readCharBlobs(inp_blob_list, perform_unit_test, char_format_list=['LLLNN', 'LLLNNN', 'LLLNNNN'],
                   inp_type='Blob', use_char_format=False):

    #Check if number of characters is valid
    format_to_use = None
    for code in char_format_list:
        if len(inp_blob_list) == len(code):
            format_to_use = code
            break

    if format_to_use is None and use_char_format:
        print "Character Recognition: No character format using %i characters" %len(inp_blob_list)
        return None

    out_char_list = []
    for index, this_blob in enumerate(inp_blob_list):

        if inp_type == 'Blob':
            character = this_blob.blobImage()
        elif inp_type == 'Image':
            character = this_blob

        if use_char_format:
            if format_to_use[index] == 'L':
                this_char_val = letter_reader.findMatch(character, perform_unit_test=perform_unit_test)

            elif format_to_use[index] == 'N':
                this_char_val = number_reader.findMatch(character, perform_unit_test=perform_unit_test)

        else:
            this_char_val = all_reader.findMatch(character, perform_unit_test=perform_unit_test)

        out_char_list.append(this_char_val)

    if not use_char_format:
        out_char_list = _correctCharList(out_char_list)

    if perform_unit_test:
        print ''.join(out_char_list)

    return out_char_list


def _correctCharList(char_list):

    override_list = [
        ('O', '0'),
        ('I', '1'),
        ('B', '8'),
        ('G', '6'),
        ('S', '5'),
        ('T', '1')
    ]

    fixed_list = char_list[:]
    split_index = (len(char_list) / 2 - 1)

    for i, char in enumerate(char_list):

        for override in override_list:

            if i <= split_index:
                if char == override[1]:
                    print char + " -> " + override[0]
                    fixed_list[i] = override[0]
                    break

            elif i > split_index:
                if char == override[0]:
                    print char + " -> " + override[1]
                    fixed_list[i] = override[1]
                    break

    return fixed_list


def _markCharFoundWithRectangles(input_image, blob_list, yLower, used_method):
    '''
    Just returns a tuple of topLeft and bottomRight to be used for
    marking rectangles
    '''
    rect_list = []
    width, height = input_image.width, input_image.height
    x_off, y_off = width * 20 / 100, height * 20 / 100

    if used_method == 'Color Sweep':
        yAdj = yLower
    elif used_method == 'Cropped Threshold Sweep':
        yAdj = yLower
    elif used_method == 'Uncropped Threshold Sweep':
        yAdj = 0
    else:
        print "ERROR! What method did you use!?"

    for char_blob in blob_list:

        x1_blob, y1_blob = char_blob.minX(), char_blob.minY()
        x2_blob, y2_blob = char_blob.maxX(), char_blob.maxY()

        x1, y1 = (x1_blob+x_off), (y1_blob+y_off+yAdj)
        x2, y2 = (x2_blob+x_off), (y2_blob+y_off+yAdj)

        rect_list.append( ((x1, y1), (x2, y2)) )

    return rect_list
