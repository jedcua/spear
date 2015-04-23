import SimpleCV
import texttable
import time
import copy
from termcolor import colored


def findChar(input_image,

             MAX_Y_GAP=7, MAX_WIDTH_GAP=7, MAX_HEIGHT_GAP=5, MAX_AR_GAP=0.078,

             MIN_ASPECT_RATIO=0.45, MAX_ASPECT_RATIO=0.77,
             MIN_SP_ASPECT_RATIO=0.08, MAX_SP_ASPECT_RATIO=0.245,
             MIN_SP2_ASPECT_RATIO=0.31, MAX_SP2_ASPECT_RATIO=0.35,
             MIN_AREA=900, MAX_AREA=float('inf'),

             MIN_COUNT=3, MAX_COUNT=7, MAX_WIDTH_MULTIPLE=10,

             perform_unit_test=False, right_click_save=False):
    #NOTE: MAX_Y_GAP=10
    """
    Method:
        Takes a binarized SimpleCV.Image, determines location of the
        Alphanumeric character, and returns a list of SimpleCV.FeatureSet
        containing the potential locations of the Alphanumeric Character.

    Parameters:

        Filtering individual Non-character Blobs:
            minAR            - Minimum Width/Height of a Blob.
            maxAR            - Maximum Width/Height of a Blob.
            minArea          - Minimum rectangular area of a Blob.
            maxArea          - Maximum rectangular area of a Blob.

        Grouping Blobs by attribute:
            maxYGap          - Highest allowed Y Pos gap between Blobs for grouping.
            maxWidthGap      - Highest allowed Width gap between Blobs for grouping.
            maxHeightGap     - Highest allowed Height gap between Blobs for grouping.

        Filtering Blob groups by their attribute:
            minCount         - Minimum allowed number of Blobs in a list.
            maxCount         - Maximum allowed number of Blobs in a list.
            maxWidthMultiple - Farthest width x N distance for an actual License Plate.

        Guessing missing character Blobs:
            guessMissing     - Perform interpolation and extrapolation for missing Blobs.
            centerPos        - Location of Center relative to Image's width x thisValue (0:Left, 1:Right)

        Debugging:
            performUnitTest  - Show visual feedback for debugging.

    Returns:
        List of SimpleCV.FeatureSet containing Blobs bounding the Alphanumeric Character.
        None is no FeatureSets remained.

    """
    if perform_unit_test: input_image.show()

    raw_blobs = input_image.findBlobs()

    #Exit function if no blobs found
    if raw_blobs is None:
        return None

    filtered_blobs = filter(lambda blob: MIN_ASPECT_RATIO <= (float(blob.width()) / float(blob.height())) <= MAX_ASPECT_RATIO, raw_blobs)
    filtered_blobs = filter(lambda blob: MIN_AREA < (blob.width() * blob.height()) < MAX_AREA, filtered_blobs)

    special_blobs = filter(lambda blob: MIN_SP_ASPECT_RATIO <= (float(blob.width()) / float(blob.height())) <= MAX_SP_ASPECT_RATIO, raw_blobs)
    if len(special_blobs):
        special_blobs = _monkeyPatchBlobs(special_blobs, input_image)
        filtered_blobs.extend(special_blobs)

    special_blobs2 = filter(lambda blob: MIN_SP2_ASPECT_RATIO <= (float(blob.width()) / float(blob.height())) <= MAX_SP2_ASPECT_RATIO, raw_blobs)
    if len(special_blobs2):
        special_blobs2 = _monkeyPatchBlobs(special_blobs2, input_image, MIN_AREA_FILLED=35)
        filtered_blobs.extend(special_blobs2)
        special_blobs.extend(special_blobs2)


    #Exit function if no blobs remain
    if len(filtered_blobs) == 0:
        return None

    list_of_blob_lists = [filtered_blobs]
    list_of_blob_lists = _regroupListOfList(list_of_blob_lists, _sortByHeight, _heightRelativeGapComparator, MAX_HEIGHT_GAP)
    list_of_blob_lists = _regroupListOfList(list_of_blob_lists, _sortByWidth, _widthRelativeGapComparator, MAX_WIDTH_GAP)
    list_of_blob_lists = _regroupListOfList(list_of_blob_lists, _sortByAspectRatio, _aspectRatioRelativeGapComparator, MAX_AR_GAP)
    list_of_blob_lists = _regroupListOfList(list_of_blob_lists, _sortByY, _yRelativeGapComparator, MAX_Y_GAP)

    list_of_char_lists = _filterAlphanumericBlobs(list_of_blob_lists, MIN_COUNT, MAX_COUNT, MAX_WIDTH_MULTIPLE)

    if len(list_of_char_lists) == 0:
        return None

    final_char_lists, blacklisted_blobs_list = _removeBlacklistCharacters(list_of_char_lists, input_image,
                                                                          blacklist_reader, threshold=40)
    final_char_lists, blacklisted_blobs_list2 = _removeBlacklistCharacters(final_char_lists, input_image,
                                                                           blacklist2_reader, threshold=85)
    blacklisted_blobs_list.extend(blacklisted_blobs_list2)

    #final_char_lists = list_of_char_lists[:]

    if perform_unit_test:
        #_animatedDisplayBlobGroups([raw_blobs], input_image, rect_color=(0, 0, 255), save_on_right_click=right_click_save)
        #_animatedDisplayBlobGroups([filtered_blobs], input_image, rect_color=(255, 255, 0), save_on_right_click=right_click_save)
        #_animatedDisplayBlobGroups([special_blobs], input_image, rect_color=(0, 255, 255), save_on_right_click=right_click_save)
        #_animatedDisplayBlobGroups(list_of_blob_lists, input_image, rect_color=(255, 0, 0), save_on_right_click=right_click_save)
        #_animatedDisplayBlobGroups(list_of_char_lists, input_image, rect_color=(0, 255, 0), save_on_right_click=right_click_save)
        #_animatedDisplayBlobGroups(blacklisted_blobs_list, input_image, rect_color=(130, 70, 0), save_on_right_click=right_click_save)
        _animatedDisplayBlobGroups(final_char_lists, input_image, rect_color=(255, 0, 255), save_on_right_click=right_click_save)

    if len(final_char_lists) == 0:
        return None
    else:
        return final_char_lists


def _printBlobListData(inp_blob_list):

    if len(inp_blob_list) == 0:
        return None

    table = texttable.Texttable()

    table.set_deco(texttable.Texttable.HEADER)
    table.set_cols_align(["r","r","r","r","r","r","r","r"])
    table.set_cols_dtype(['i','i','i','i','f','i','d','f'])

    table_label = ["X","Y","W","H","Aspect Ratio","RectArea","BlobArea","Rect/Blob"]
    rows = [table_label]

    for blob in inp_blob_list:
        aspect_ratio = float(blob.width()) / float(blob.height())
        rect_area = int(blob.width() * blob.height())
        rows.append([blob.x, blob.y, blob.width(), blob.height(),
                     aspect_ratio, rect_area, blob.area(),
                     float(rect_area)/blob.area()])

    table.add_rows(rows)
    print table.draw()

    sum_y, sum_w, sum_h = float(0),float(0),float(0)
    num_item = len(inp_blob_list)

    for blob in inp_blob_list:
        sum_y += blob.y
        sum_w += blob.width()
        sum_h += blob.height()

    #Get average statistics
    ave_y, ave_w, ave_h = sum_y / num_item, sum_w / num_item, sum_h / num_item

    print "_________________________"
    print "Ave Y Pos : " + str(ave_y)
    print "Ave Width : " + str(ave_w)
    print "Ave Height: " + str(ave_h)
    print "Ave AR    : " + str(ave_w/ave_h)
    print "Num Blobs : " + str(len(inp_blob_list))
    print "_________________________"


def _animatedDisplayBlobGroups(this_list_of_list, target_img, rect_color=(255,0,0), text_color=(255, 0, 0),
                               retain=False, save_on_right_click=False):

    display = SimpleCV.Display((target_img.width, target_img.height), title="SPEAR")

    print "Number of Blob Groups:" + str(len(this_list_of_list))

    for this_list in this_list_of_list:

        target_img = _markBlobsWithRectangles(this_list, target_img, rect_color, text_color, retain)
        print "\n"
        _printBlobListData(sorted(this_list, key = lambda blob: blob.x))

        target_img.save(display)

        while not display.isDone():

            if display.mouseLeft:
                display.done = True

            #Save all char blobs if right_click_save=True
            if save_on_right_click and display.mouseRight:

                for index, this_blob in enumerate(this_list):
                    this_blob.blobImage().save(str(index) + ".jpg")

                print str(index + 1) + " Images saved."
                time.sleep(0.2)

        time.sleep(0.1)
        display.done = False


def _markBlobsWithRectangles(input_blob_list, target_img, rect_color=(255, 0, 0),
                             text_color=(255, 255, 255), retain_prev=False):

    #May cause warnings if removing a nonexistent Drawing Layer. Just ignore ;)
    if retain_prev == False:
        target_img.removeDrawingLayer()

    for blob in input_blob_list:
        x1, y1 = blob.minX(), blob.minY()
        x2, y2 = blob.maxX(), blob.maxY()

        target_img.dl().rectangle2pts((x1, y1), (x2, y2), rect_color, 2, False)
        target_img.dl().text(str(blob.x) + "," + str(blob.y), (x1, y1 - 15), text_color)

    return target_img


def _regroupListOfList(inp_list_of_list, sort_function, compare_function, COMPARATOR_PARAMETER):

    final_list_of_list = []

    for this_list in inp_list_of_list:
        temp_list_of_list = _groupBlobListWithCategory(this_list, sort_function, compare_function, COMPARATOR_PARAMETER)
        final_list_of_list.extend(temp_list_of_list)

    return final_list_of_list


def _groupBlobListWithCategory(inp_blob_list, sort_function, compare_function, COMPARATOR_PARAMETER):

    #Sort according to desired category
    inp_blob_list = sort_function(inp_blob_list)

    list_of_blob_lists = []
    this_feature_set = SimpleCV.FeatureSet()

    #Off by 1 bug ;)
    this_feature_set.append(inp_blob_list[0])

    #Segregate blob list according to specified condition in compareFunction
    for blob_index in range(1, len(inp_blob_list)):

        prev_blob = inp_blob_list[blob_index - 1]
        current_blob = inp_blob_list[blob_index]

        #If yes, put it on the same list
        if (compare_function(current_blob, prev_blob, COMPARATOR_PARAMETER)):
            this_feature_set.append(current_blob)

        #if no, put it on a new list
        else:

            list_of_blob_lists.append(this_feature_set)
            this_feature_set = SimpleCV.FeatureSet()
            this_feature_set.append(current_blob)

    #Last thisFeatureSet won't be appended. So append it ;)
    list_of_blob_lists.append(this_feature_set)

    return list_of_blob_lists


def _sortByY(this_list):

    return sorted(this_list, key = lambda blob: blob.y)


def _yRelativeGapComparator(this_current_blob, this_prev_blob, MAX_Y_GAP):

    if ((this_current_blob.y - this_prev_blob.y) <= MAX_Y_GAP):
        return True

    else:
        return False


def _sortByWidth(this_list):

    sorted_list = sorted(this_list, key = lambda blob: blob.width())
    return sorted_list


def _widthRelativeGapComparator(this_current_blob, this_prev_blob, MAX_WIDTH_GAP):

    if ((this_current_blob.width() -  this_prev_blob.width()) <= MAX_WIDTH_GAP):
        return True

    else:
        return False


def _sortByHeight(this_list):

    sorted_list = sorted(this_list, key = lambda blob: blob.height())
    return sorted_list


def _heightRelativeGapComparator(this_current_blob, this_prev_blob, MAX_HEIGHT_GAP):

    if ((this_current_blob.height() - this_prev_blob.height()) <= MAX_HEIGHT_GAP):
        return True

    else:
        return False


def _sortByAspectRatio(this_list):

    sorted_list = sorted(this_list, key = lambda blob: float(blob.width()) / blob.height())
    return sorted_list


def _aspectRatioRelativeGapComparator(this_current_blob, this_prev_blob, MAX_AR_GAP):
    current_blob_AR = float(this_current_blob.width()) / this_current_blob.height()
    prev_blob_AR = float(this_prev_blob.width()) / this_prev_blob.height()

    if ((current_blob_AR - prev_blob_AR) <= MAX_AR_GAP):
        return True

    else:
        return False


def _filterAlphanumericBlobs(inp_list_of_lists, MIN_COUNT, MAX_COUNT, MAX_WIDTH_MULTIPLE):

    out_list_of_lists = []

    for this_list in inp_list_of_lists:

        if (MIN_COUNT <= len(this_list) <= MAX_COUNT):

            this_list = this_list.sortX()

            #Get edges and average width
            first_blob_left_edge = this_list[0].minX()
            last_blob_right_edge = this_list[-1].maxX()

            sum_width = float(0)

            for this_blob in this_list:

                sum_width += this_blob.width()

            ave_width = sum_width / len(this_list)

            if ((last_blob_right_edge - first_blob_left_edge) <= (ave_width * MAX_WIDTH_MULTIPLE)):
                out_list_of_lists.append(this_list)

    return out_list_of_lists


def _clip(val, min_val, max_val):

    if val < min_val:
        val = min_val

    elif val > max_val:
        val = max_val

    return val


def _monkeyPatchBlobs(input_blobs, input_image, MIN_AREA_FILLED=45):

    out_blobs = SimpleCV.FeatureSet()
    for blob in input_blobs:
        new_blob = _overrideBlob(blob, input_image, MIN_AREA_FILLED)
        out_blobs.append(new_blob)

    return out_blobs


def _overrideBlob(input_blob, input_image, MIN_AREA_FILLED, DESIRED_AR=0.59):

    x_boundL, x_boundU = 0, input_image.width-1

    orig_x, orig_y = input_blob.x, input_blob.y
    orig_width = input_blob.width()
    orig_height = input_blob.height()


    #Check first if blob's shape is rectangular
    perc_filled = (float(input_blob.area()) / (orig_width * orig_height)) * 100

    if perc_filled < MIN_AREA_FILLED:
        return input_blob

    print colored("Special Blob : (%i, %i) : %f filled" %(orig_x, orig_y, perc_filled),
                  color='yellow', on_color='on_blue', attrs=['bold'])

    #if not input_blob.isRectangle(0.08):
    #    return input_blob

    new_width = int(DESIRED_AR * orig_height)
    new_minX = _clip(orig_x - (new_width / 2), x_boundL, x_boundU)
    new_maxX = _clip(orig_x + (new_width / 2), x_boundL, x_boundU)
    new_blobMask = input_image[int(new_minX):int(new_maxX), orig_y:orig_y+orig_height]

    #Define new method and attribute for width
    blob = copy.copy(input_blob)

    blob.width = lambda : new_width
    blob.minX = lambda : new_minX
    blob.maxX = lambda : new_maxX
    blob.blobImage = lambda : new_blobMask
    blob.blobMask = lambda : new_blobMask

    return blob

#-------------------------------------------------------------------------------------------
import charRecog
import os

prog_path = os.path.dirname(os.path.realpath(__file__))

blacklist_path = prog_path + "/template/blacklist/"
blacklist_reader = charRecog.CharReader(blacklist_path)

blacklist2_path = prog_path + "/template/blacklist2/"
blacklist2_reader = charRecog.CharReader(blacklist2_path)


def _removeBlacklistCharacters(input_blobs, input_image, charReader, threshold, debug=False):

    retained_list = []
    removed_list = []
    for blob in input_blobs[0]:
        x1, y1 = blob.minX(), blob.minY()
        x2, y2 = blob.maxX(), blob.maxY()

        otsu_char = input_image[x1:x2, y1:y2]

        reading = charReader.findMatch(otsu_char, threshold, perform_unit_test=debug)

        if reading == '?':
            retained_list.append(blob)
        else:
            removed_list.append(blob)

    num_removed = (len(input_blobs[0]) - len(retained_list))

    if num_removed > 0:
        print colored("Blacklisted: %i" %num_removed,
                              on_color='on_green', attrs=['bold'])

    if len(retained_list):
        return [retained_list], [removed_list]
    else:
        return [retained_list], []

