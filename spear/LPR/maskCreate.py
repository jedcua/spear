import sklearn.cluster


def colorSegmentation(input_image, NUM_CLUSTERS=7, RANGE_OFFSET=30, SCALE_FACTOR=0.1,
                      use_fast_KMeans=False, perform_unit_test=False,
                      right_click_save=False):

    """
    Method:
        Takes a SimpleCV.Image, computes the most dominant colors
        using K-Means clustering, and returns a list of SimpleCV.Image
        binary masks using the dominant color.

    Parameters:
        input_image       - Input image to be used.
        NUM_CLUSTERS      - Number of Clusters (k) for K-Means algortihm.
        RANGE_OFFSET      - Minimum and maximum deviation from the RGB center.
        SCALE_FACTOR      - Applies scaling to reduce processing delay at cost of accuracy loss.
        use_fast_KMeans   - Use Mini Batch KMeans for faster processing at cost of accuracy loss.
        perform_unit_test - Used for debugging.
        right_click_save  - Right click saves image in Unit Test mode.

    Returns:
        List of SimpleCV.Image with applied binary mask.
    """

    #For some reason, scale method doesn't yield expected result with Kmeans :/
    scaled_image = input_image.resize(int(input_image.width * SCALE_FACTOR),
                                      int(input_image.height * SCALE_FACTOR))

    raw_RGB_list = _toPixelArray(scaled_image)

    clustered_RGB_list = _getDominantColors(raw_RGB_list, NUM_CLUSTERS, use_fast_KMeans)

    color_mask_list = _makeBinaryMasks(input_image, clustered_RGB_list, RANGE_OFFSET)

    if perform_unit_test:
        _unitTest(input_image, raw_RGB_list, clustered_RGB_list,
                  color_mask_list, right_click_save)

    return color_mask_list


def thresholdSweep(input_image, MIN_THRESHOLD=0, MAX_THRESHOLD=255,
                   THRESH_STEP=10, use_rgb_mask=False):
    """
    Method:
        Creates list of SimpleCV.Image masks using Threshold Sweeping.

    Parameters:
        input_image   - Image to use in generating masks.
        MIN_THRESHOLD - Lower boundary of the sweep.
        MAX_THRESHOLD - Upper boundary of the sweep.
        THRESH_STEP   - Incremental value from lower to upper boundary.
        use_rgb_mask  - Use RGB channels of an image rather than just the grayscale.

    Returns:
        List of SimpleCV.Image, the Masks generated.

    """
    #Returns a Generator!
    make_mask = lambda (this_img): _createMaskThresholdSweep(this_img, MIN_THRESHOLD, MAX_THRESHOLD, THRESH_STEP)

    if not use_rgb_mask:
        return make_mask(input_image)

    else:
        combined_masks = []

        r, g, b = input_image.splitChannels()
        #This ruins the generator (i think) by turning it to a list?
        combined_masks.extend(make_mask(r))
        combined_masks.extend(make_mask(g))
        combined_masks.extend(make_mask(b))

        return combined_masks


def _unitTest(input_image, raw_RGB_list, clustered_RGB_list, color_mask_list, save_on_right_click):

    import SimpleCV
    import time

    display = SimpleCV.Display((input_image.width, input_image.height))

    print "Extracted " + str(len(clustered_RGB_list)) + " colors."

    for  index, this_mask in enumerate(color_mask_list):

        print clustered_RGB_list[index]
        this_mask.save(display)

        while not display.isDone():
            if display.mouseLeft:
                display.done = True
                time.sleep(0.2)

            elif display.mouseRight and save_on_right_click:
                this_mask.save(str(index) + ".jpg")
                print "Image saved."
                time.sleep(0.2)

        display.done = False


def _toPixelArray(input_image):

    RGB_pixel_matrix = input_image.getNumpy()

    RGB_pixel_array = RGB_pixel_matrix.reshape(
        (RGB_pixel_matrix.shape[0] * RGB_pixel_matrix.shape[1],
         3))

    return RGB_pixel_array


def _getDominantColors(RGB_array, NUM_CLUSTERS, use_mini_batch):

    if use_mini_batch:
        cluster_method = sklearn.cluster.MiniBatchKMeans(NUM_CLUSTERS)
    else:
        cluster_method = sklearn.cluster.KMeans(n_clusters = NUM_CLUSTERS)

    cluster_method.fit(RGB_array)

    RGB_list = cluster_method.cluster_centers_[:]

    return  RGB_list


def _makeBinaryMasks(input_image, RGB_color_list, RGB_OFFSET):

    mask_list = []

    for this_RGB in RGB_color_list:

        RGB_min = map(lambda val: _addSub(val, -RGB_OFFSET), this_RGB)
        RGB_max = map(lambda val: _addSub(val, RGB_OFFSET), this_RGB)

        this_mask = input_image.createBinaryMask(RGB_min, RGB_max)
        mask_list.append(this_mask)

    return mask_list


def _addSub(inp_val, oper_val):

    inp_val += oper_val

    if inp_val < 0:
        inp_val = 0
    elif inp_val > 255:
        inp_val = 255

    return inp_val


def _createMaskThresholdSweep(inp_image, LOW_BOUND, UPPER_BOUND, INCREMENT):

    for thresh in xrange(LOW_BOUND, UPPER_BOUND + 1, INCREMENT):
        yield inp_image.threshold(thresh).invert().dilate().erode()

