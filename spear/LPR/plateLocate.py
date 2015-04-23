import SimpleCV
import math
import time
import itertools

def findPlate(
        input_image,

        INIT_THRESH=35,
        END_THRESH=5,
        THRESH_STEP=-5,

        CANNY_THRESH1=60,

        INIT_CANNY_THRESH2=200,
        END_CANNY_THRESH2=140,
        STEP_CANNY_THRESH2=-10,

        MAX_HORZ_LINE_GAP=1,
        MAX_VERT_LINE_GAP=9,

        use_std_hough=False,

        MAX_HORZ_LINE_ANGLE=5,
        MIN_VERT_LINE_ANGLE=90,

        HORZ_SCALE_FACTOR=5.0,
        VERT_SCALE_FACTOR=4.0,

        X_MERGE_GAP=5,
        Y_MERGE_GAP=5,

        MAX_HORZ_POINT_ANGLE=4,
        MIN_VERT_POINT_ANGLE=85,

        MIN_ASPECT_RATIO=2.62,
        MAX_ASPECT_RATIO=3.1,

        MIN_AREA=20000,
        MAX_AREA=float('inf'),

        POINT_RADIUS=50,

        perform_unit_test=False,
        right_click_save=False):
    """
    Method:
        Determines the location of the License Plate from inputImage and returns
        a list of Rectangle objects bounding the possible location of the License Plate

    Parameters:

        inputImage               - Input Image to be used.

        Line Detection:
            INIT_THRESH          - Initial Threshold value for Hough Transform.
            END_THRESH           - Final Threshold value for Hough Transform.
            THRESH_STEP          - Increment/Decrement value from Initial to Final.
            CANNY_THRESH1        - Parameter for internal Canny Line Detection.
            CANNY_THRESH2        - Parameter for internal Canny Line Detection.
            MAX_HORZ_LINE_GAP    - Maximum pixel distance between segments to consider them the same line.
            MAX_VERT_LINE_GAP    - Maximum pixel distance between segments to consider them the same line.
            use_std_hough        - Use Standard Hough Transform for line detection.
            MAX_HORZ_LINE_ANGLE  - Maximum angle for a line to be still considered horizontal.
            MIN_VERT_LINE_ANGLE  - Minimum angle for a line to be still considered vertical.
            HORZ_SCALE_FACTOR    - Scale factor for stretching horizontal lines.
            VERT_SCALE_FACTOR    - Scale factor for stretching vertical lines.

        Rectangle Detection:
            X_MERGE_GAP          - Farthest X Position gap between points for grouping.
            Y_MERGE_GAP          - Farthest Y Position gap between poinst for grouping.
            MAX_HORZ_POINT_ANGLE - Maximum allowed angle formed by 2 points for detecting quadrelaterals.
            MIN_VERT_POINT_ANGLE - Minimum allowed angle formed by 2 points for detecting quadrelaterals.
            MIN_ASPECT_RATIO     - Smallest Aspect ratio of quadrelateral allowed.
            MAX_ASPECT_RATIO     - Largest Aspect ratio of quadrelateral allowed.
            MIN_AREA             - Smallest Area of quadrelateral allowed.
            MAX_AREA             - Largest Area of quadrelateral allowed.
            POINT_RADIUS         - Maximum pixel distance between corners for merging quadrelaterals.

        Testing/Debugging:
            perform_unit_test    - Perform Unit Testing for debugging.
            right_click_save     -  Allows saving an image by Right-click during Unit Testing.

    Returns:
        Rectangle object List containing coordinates for possible License Plate locations.
        None if list is empty.

    """

    sum_horz_lines = SimpleCV.FeatureSet()
    sum_vert_lines = SimpleCV.FeatureSet()

    hough_threshold_list = xrange(INIT_THRESH, END_THRESH, THRESH_STEP)
    canny_thresh2_list = xrange(INIT_CANNY_THRESH2, END_CANNY_THRESH2, STEP_CANNY_THRESH2)

    zip_param_list = itertools.izip(hough_threshold_list, canny_thresh2_list)

    for current_line_thresh, current_canny_thresh2 in zip_param_list:

        if perform_unit_test:
            print "\nLine Threshold: %i, Canny Thresh2: %i" %(current_line_thresh, current_canny_thresh2)

        horz_lines, vert_lines = _detectLines(
            input_image,

            current_line_thresh,
            MAX_HORZ_LINE_GAP,
            HORZ_SCALE_FACTOR,
            MAX_HORZ_LINE_ANGLE,

            current_line_thresh,
            MAX_VERT_LINE_GAP,
            VERT_SCALE_FACTOR,
            MIN_VERT_LINE_ANGLE,

            CANNY_THRESH1,
            current_canny_thresh2,

            use_std_hough,
            perform_unit_test)

        #TODO: Make a function parameter to retain prev lines or not.
        sum_horz_lines.extend(horz_lines)
        sum_vert_lines.extend(vert_lines)
        #sum_horz_lines = horz_lines
        #sum_vert_lines = vert_lines

        out_rect_list = _detectRectangles(
            input_image,

            sum_horz_lines,
            sum_vert_lines,

            X_MERGE_GAP,
            Y_MERGE_GAP,

            MAX_HORZ_POINT_ANGLE,
            MIN_VERT_POINT_ANGLE,

            MAX_ASPECT_RATIO,
            MIN_ASPECT_RATIO,
            MIN_AREA,
            MAX_AREA,

            POINT_RADIUS,

            perform_unit_test,
            (CANNY_THRESH1, current_canny_thresh2),
            right_click_save)

        if len(out_rect_list):
            return out_rect_list

    #If still nothing found return None
    return None


# TODO: Please refactor this method ;)
def _unitTest(input_image, CANNY_THRESH_TUPLE, horz_lines, vert_lines, intersections,
              ave_intersections, rect_obj_list, merged_rect_obj_list, allow_save_right_click):
    """
    Method:
        Draws on the image to show lines, points, and polygons based on the result
        of getPlate algortihm.

        1. Draws all detected lines from SimpleCV.Image.getLines method.
        2. Draws all points from the intersection of those lines.
        3. Iterates all possible combination of points to form a quadrelateral.
        4. Draws only the accepted quadrelateral.
    """

    def _iterateDrawRectangles(inp_rect_list, rect_color, right_click_save):

        for index, this_rect in enumerate(inp_rect_list):

            print "Aspect Ratio: " + str(this_rect.aspectRatio) + " Area: " + str(this_rect.area)

            rect_layer = SimpleCV.DrawingLayer(
                (input_image.width, input_image.height))

            rect_points = [
                this_rect.topLeft,
                this_rect.topRight,
                this_rect.bottomRight,
                this_rect.bottomLeft]

            ave_rect_points = (this_rect.aveTopLeft, this_rect.aveBottomRight)

            # Draw rectangle
            rect_layer.polygon(
                rect_points,
                rect_color,
                width=0,
                filled=True,
                alpha=75)

            rect_layer.rectangle2pts(
                ave_rect_points[0], ave_rect_points[1], (0, 0, 255), 2)

            input_image.addDrawingLayer(horz_lines_layer)
            input_image.addDrawingLayer(vert_lines_layer)
            input_image.addDrawingLayer(intersection_layer)
            input_image.addDrawingLayer(ave_intersection_layer)
            input_image.addDrawingLayer(rect_layer)

            input_image.save(test_display)

            while not test_display.isDone():
                if test_display.mouseLeft:
                    test_display.done = True

                if test_display.mouseRight and right_click_save:

                    input_image.crop(
                        this_rect.topLeft,
                        this_rect.bottomRight).save(
                        str(index) +
                        ".jpg")

                    print "Image saved."
                    time.sleep(0.2)

            test_display.done = False

            input_image.clearLayers()
            input_image.removeDrawingLayer()
            input_image.removeDrawingLayer()

    test_display = SimpleCV.Display((input_image.width, input_image.height), title="SPEAR")

    # Display first the output of Edge Detection algortihm
    edge_map_img = input_image.edges(CANNY_THRESH_TUPLE[0], CANNY_THRESH_TUPLE[1])
    edge_map_img.save(test_display)

    while not test_display.isDone():
        if test_display.mouseLeft:
            test_display.done = True
    test_display.done = False

    horz_lines_layer = SimpleCV.DrawingLayer(
        (input_image.width, input_image.height))

    vert_lines_layer = SimpleCV.DrawingLayer(
        (input_image.width, input_image.height))

    intersection_layer = SimpleCV.DrawingLayer(
        (input_image.width, input_image.height))

    ave_intersection_layer = SimpleCV.DrawingLayer(
        (input_image.width, input_image.height))

    for line in horz_lines:

        x1, y1 = line.topLeftCorner()
        x2, y2 = line.bottomRightCorner()

        horz_lines_layer.line((x1, y1), (x2, y2), (0, 255, 0), 2)

    for line in vert_lines:

        x1, y1 = line.topLeftCorner()
        x2, y2 = line.bottomRightCorner()

        vert_lines_layer.line((x1, y1), (x2, y2), (255, 255, 0), 2)

    for point in intersections:

        x = int(point[0])
        y = int(point[1])

        intersection_layer.circle((x, y), 2, (255, 0, 0), 0, True)

    for point in ave_intersections:

        x = int(point[0])
        y = int(point[1])

        ave_intersection_layer.circle((x, y), 20, (0, 0, 255), 2)

    input_image.addDrawingLayer(horz_lines_layer)
    input_image.addDrawingLayer(vert_lines_layer)
    input_image.addDrawingLayer(intersection_layer)
    input_image.addDrawingLayer(ave_intersection_layer)

    input_image.save(test_display)

    while not test_display.isDone():
        if test_display.mouseLeft:
            test_display.done = True
    test_display.done = False

    input_image.clearLayers()
    input_image.removeDrawingLayer()
    input_image.removeDrawingLayer()

    _iterateDrawRectangles(rect_obj_list, (255, 0, 0), allow_save_right_click)

    _iterateDrawRectangles(merged_rect_obj_list, (0, 0, 255), allow_save_right_click)


class Rectangle:

    def __init__(self, cornerDict):

        # Imperfect Corners
        self.topLeft = cornerDict.get("topLeft")
        self.topRight = cornerDict.get("topRight")
        self.bottomRight = cornerDict.get("bottomRight")
        self.bottomLeft = cornerDict.get(("bottomLeft"))

        # Averaged Borders
        self.aveMinX = (self.topLeft[0] + self.bottomLeft[0]) / 2
        self.aveMaxX = (self.topRight[0] + self.bottomRight[0]) / 2
        self.aveMinY = (self.topLeft[1] + self.topRight[1]) / 2
        self.aveMaxY = (self.bottomLeft[1] + self.bottomRight[1]) / 2

        # Averaged Corners
        self.aveTopLeft = (self.aveMinX, self.aveMinY)
        self.aveBottomRight = (self.aveMaxX, self.aveMaxY)

        # Dimensions
        self.aveWidth = self.aveMaxX - self.aveMinX
        self.aveHeight = self.aveMaxY - self.aveMinY

        self.aspectRatio = float(self.aveWidth) / float(self.aveHeight)
        self.area = float(self.aveWidth) * float(self.aveHeight)


def _detectLines(
        input_image,
        HORZ_THRESHOLD,
        MAX_HORZ_LINE_GAP,
        HORZ_SCALE_FACTOR,
        MAX_HORZ_LINE_ANGLE,
        VERT_THRESHOLD,
        MAX_VERT_LINE_GAP,
        VERT_SCALE_FACTOR,
        MIN_VERT_LINE_ANGLE,
        CANNY_THRESH1,
        CANNY_THRESH2,
        use_std_hough,
        perform_unit_test):

    # Note: useStandard=True produces better vert line detection ;) but slower
    lines_h = input_image.findLines(
        threshold=HORZ_THRESHOLD,
        useStandard=use_std_hough,
        maxlinegap=MAX_HORZ_LINE_GAP,
        cannyth1=CANNY_THRESH1,
        cannyth2=CANNY_THRESH2)

    lines_v = input_image.findLines(
        threshold=VERT_THRESHOLD,
        useStandard=use_std_hough,
        maxlinegap=MAX_VERT_LINE_GAP,
        cannyth1=CANNY_THRESH1,
        cannyth2=CANNY_THRESH2)

    if perform_unit_test:
        print "\nFound Lines - Horizontal: " + str(len(lines_h)) + " Vertical: " + str(len(lines_v))

    lines_h = _extendLines(lines_h, input_image, HORZ_SCALE_FACTOR)
    lines_v = _extendLines(lines_v, input_image, VERT_SCALE_FACTOR)

    if perform_unit_test:
        print "Extended Lines - Horizontal:" + str(HORZ_SCALE_FACTOR) + " Vertical: " + str(VERT_SCALE_FACTOR)

    horz_lines, __ = _filterOrtogonalLines(
        lines_h, MAX_HORZ_LINE_ANGLE, MIN_VERT_LINE_ANGLE)

    __, vert_lines = _filterOrtogonalLines(
        lines_v, MAX_HORZ_LINE_ANGLE, MIN_VERT_LINE_ANGLE)

    if perform_unit_test:
        print "Found Ortogonal Lines - Horizontal: " + str(len(horz_lines)) + " Vertical: " + str(len(vert_lines))

    return (horz_lines, vert_lines)


def _detectRectangles(
        input_image,
        horz_lines,
        vert_lines,
        X_MERGE_GAP,
        Y_MERGE_GAP,
        MAX_HORZ_POINT_ANGLE,
        MIN_VERT_POINT_ANGLE,
        MAX_ASPECT_RATIO,
        MIN_ASPECT_RATIO,
        MIN_AREA,
        MAX_AREA,
        POINT_RADIUS,
        perform_unit_test,
        CANNY_THRESH_TUPLE,
        right_click_save):

    intersections = _findIntersections(horz_lines, vert_lines)

    if perform_unit_test:
        print "Found Intersections: " + str(len(intersections)) + " intersections"

    intersections = list(set(intersections))

    if perform_unit_test:
        print "Remove Duplicate Intersections: " + str(len(intersections)) + " intersections"

    list_of_intersections = [intersections]

    list_of_intersections = _regroupListOfList(
        list_of_intersections,
        _sortByY,
        _yRelativeGapComparator,
        Y_MERGE_GAP)

    list_of_intersections = _regroupListOfList(
        list_of_intersections,
        _sortByX,
        _xRelativeGapComparator,
        X_MERGE_GAP)

    if perform_unit_test:
        print "Grouped Intersections: " + str(len(list_of_intersections)) + " groups"

    ave_intersections = _averageIntersections(list_of_intersections)

    if perform_unit_test:
        print "Averaged Intersections: " + str(len(ave_intersections)) + " intersections"

    rect_obj_list = _findQuadPoints(
        ave_intersections,
        MAX_HORZ_POINT_ANGLE,
        MIN_VERT_POINT_ANGLE)

    if perform_unit_test:
        print "Found Rectangles: " + str(len(rect_obj_list)) + " rectangles"

    rect_obj_list = filter(
        lambda thisRect: MAX_ASPECT_RATIO > thisRect.aspectRatio > MIN_ASPECT_RATIO,
        rect_obj_list)

    rect_obj_list = filter(
        lambda this_rect: MAX_AREA > this_rect.area > MIN_AREA,
        rect_obj_list)

    if perform_unit_test:
        print "Retained Accepted Rectangles: " + str(len(rect_obj_list)) + " rectangles"

    rect_obj_list = sorted(rect_obj_list, key=lambda this_rect: this_rect.area)

    if perform_unit_test:
        print "Sorted  Rectangles"

    merged_rect_obj_list = _mergeOverlapRect(rect_obj_list, POINT_RADIUS)

    if perform_unit_test:
        print "Merged Rectangles: " + str(len(merged_rect_obj_list)) + " rectangles\n"

    # Perform unit Testing
    if perform_unit_test:
        _unitTest(
            input_image,
            CANNY_THRESH_TUPLE,
            horz_lines,
            vert_lines,
            intersections,
            ave_intersections,
            rect_obj_list,
            merged_rect_obj_list,
            right_click_save)

    return merged_rect_obj_list


def _filterOrtogonalLines(line_list, MAX_HORZ_ANGLE, MIN_VERT_ANGLE):

    horz_filter = lambda line : abs(line.angle()) <= MAX_HORZ_ANGLE
    vert_filter = lambda line : abs(line.angle()) >= MIN_VERT_ANGLE

    horz_lines = filter(horz_filter, line_list)
    vert_lines = filter(vert_filter, line_list)

    return (horz_lines, vert_lines)


def _extendLines(line_list, input_image, SCALE_FACTOR):

    out_list = SimpleCV.FeatureSet()

    for this_line in line_list:

        x_center, y_center = this_line.x, this_line.y

        angle_in_rad = math.radians(this_line.angle())

        hypothenus = float((this_line.length() * SCALE_FACTOR) / 2)
        opposite = float(math.sin(angle_in_rad) * hypothenus)
        adjacent = float(math.cos(angle_in_rad) * hypothenus)

        x1, y1 = x_center - adjacent, y_center - opposite
        x2, y2 = x_center + adjacent, y_center + opposite

        new_line = SimpleCV.Line(input_image, ((x1, y1), (x2, y2)))

        out_list.append(new_line)

    return out_list


def _findIntersections(horz_lines, vert_lines):

    intersections = []
    line_iter = itertools.product(horz_lines, vert_lines)

    for horz_line, vert_line in line_iter:
        x_lower, x_upper = horz_line.minX(), horz_line.maxX()
        y_lower, y_upper = vert_line.minY(), vert_line.maxY()

        if (x_lower < vert_line.x < x_upper) and (y_lower < horz_line.y < y_upper):
            intersection = horz_line.findIntersection(vert_line)
            intersections.append(intersection)

    return intersections


def _regroupListOfList(inp_list_of_list, sort_function, compare_function, GAP):

    final_list_of_list = []

    for this_list in inp_list_of_list:
        temp_list_of_list = _groupPointListWithCategory(
            this_list,
            sort_function,
            compare_function,
            GAP)

        final_list_of_list.extend(temp_list_of_list)

    return final_list_of_list


def _groupPointListWithCategory(point_list, sort_function, compare_function, GAP):

    # Check if not empty List
    if not len(point_list):
        return []

    # Sort according to desired category
    point_list = sort_function(point_list)

    list_of_point_lists = []
    this_set = []

    # Off by 1 bug ;)
    this_set.append(point_list[0])

    # Segregate pointList according to specified condition in compareFunction
    for point_index in xrange(1, len(point_list)):

        prev_point = point_list[point_index - 1]
        current_point = point_list[point_index]

        # If yes, put it on the same list
        if (compare_function(current_point, prev_point, GAP)):
            this_set.append(current_point)

        # if no, put it on a new list
        else:
            list_of_point_lists.append(this_set)
            this_set = []
            this_set.append(current_point)

    # Last this_set won't be appended. So append it ;)
    list_of_point_lists.append(this_set)

    return list_of_point_lists


def _sortByY(point_list):
    return sorted(point_list, key=lambda point: point[1])


def _yRelativeGapComparator(current_point, prev_point, GAP):

    if ((current_point[1] - prev_point[1]) <= GAP):
        return True
    else:
        return False


def _sortByX(point_list):
    return sorted(point_list, key=lambda point: point[0])


def _xRelativeGapComparator(current_point, prev_point, GAP):

    if ((current_point[0] - prev_point[0]) <= GAP):
        return True
    else:
        return False


def _averageIntersections(list_of_list):

    out_list = []

    for this_list in list_of_list:
        sum_x, sum_y = 0, 0

        for x, y in this_list:
            sum_x += x
            sum_y += y

        out_list.append((sum_x / len(this_list),
                         sum_y / len(this_list)))

    return out_list


def _findQuadPoints(intersection_list, MAX_HORZ_ANGLE, MIN_VERT_ANGLE):

    combination_point_list = itertools.combinations(intersection_list, 4)
    rect_obj_list = []

    for point_list in combination_point_list:
        corners = {}

        for this_point in point_list:
            other_points = list(point_list)
            other_points.remove(this_point)

            corner_map = _isCornerPoint(this_point, other_points,
                                        MAX_HORZ_ANGLE, MIN_VERT_ANGLE)

            if corner_map:
                key = ''
                if corner_map == (-1, -1):
                    key = 'topLeft'
                elif corner_map == (-1, 1):
                    key = 'bottomLeft'
                elif corner_map == (1, -1):
                    key = 'topRight'
                elif corner_map == (1, 1):
                    key = 'bottomRight'

                corners[key] = this_point

            # Don't waste time iterating if any 1 isn't a corner anyway
            elif corner_map is None:
                break

        # There should be 4 corners only.
        if len(corners) == 4:
            this_rect = Rectangle(corners)
            rect_obj_list.append(this_rect)

    return rect_obj_list


def _isCornerPoint(this_point, other_points,
                   MAX_HORZ_ANGLE, MIN_VERT_ANGLE):

    num_horz_adj_points, num_vert_adj_points = 0, 0
    horz_sign, vert_sign = '', ''

    x1, y1 = this_point

    for x2, y2 in other_points:

        diff_X = float(x1 - x2)
        diff_Y = float(y1 - y2)

        #Vertical lines are 90 degress. Cant divide by 0
        if ((diff_X == 0) and (diff_Y != 0)):
            angle = 90
        else:
            angle = abs(math.degrees(math.atan(diff_Y / diff_X)))

        if angle <= MAX_HORZ_ANGLE:
            num_horz_adj_points += 1
            horz_sign = cmp(diff_X, 0)

        elif angle >= MIN_VERT_ANGLE:
            num_vert_adj_points += 1
            vert_sign = cmp(diff_Y, 0)

        #Early exit to speed up processing
        if (num_horz_adj_points > 1) or (num_vert_adj_points > 1):
            return None

    # There should only be 1 horizontal and vertical adjacent point
    if (num_horz_adj_points, num_vert_adj_points) == (1, 1):
        return (horz_sign, vert_sign)
    else:
        return None


def _mergeOverlapRect(inp_rect_obj_list, RADIUS):

    #Group overlapping rectangles
    list_of_rect_list = []
    rect_obj_list = inp_rect_obj_list[:]

    while len(rect_obj_list):
        this_rect = rect_obj_list.pop(0)
        other_rect_list = rect_obj_list[:]

        this_overlap_list = [this_rect]

        for other_rect in list(set(other_rect_list)):
            if _isOverlapping(this_rect, other_rect, RADIUS):
                this_overlap_list.append(other_rect)
                rect_obj_list.remove(other_rect)

        list_of_rect_list.append(this_overlap_list)

    #Then compute average of each group
    out_rect_list = []

    for this_rect_list in list_of_rect_list:
        sum_x1, sum_y1 = 0, 0
        sum_x2, sum_y2 = 0, 0

        for this_rect in this_rect_list:
            sum_x1 += this_rect.aveMinX
            sum_y1 += this_rect.aveMinY
            sum_x2 += this_rect.aveMaxX
            sum_y2 += this_rect.aveMaxY

        num_rect = len(this_rect_list)

        ave_x1 = int(sum_x1 / num_rect)
        ave_y1 = int(sum_y1 / num_rect)
        ave_x2 = int(sum_x2 / num_rect)
        ave_y2 = int(sum_y2 / num_rect)

        corner_dict = {}
        corner_dict['topLeft'] = ave_x1, ave_y1
        corner_dict['topRight'] = ave_x2, ave_y1
        corner_dict['bottomLeft'] = ave_x1, ave_y2
        corner_dict['bottomRight'] = ave_x2, ave_y2

        new_rect = Rectangle(corner_dict)

        out_rect_list.append(new_rect)

    return out_rect_list


def _isOverlapping(this_rect, other_rect, RADIUS):

    # Topleft corners of two rectangles
    diff_X1 = abs(this_rect.aveMinX - other_rect.aveMinX)
    diff_Y1 = abs(this_rect.aveMinY - other_rect.aveMinY)

    # BottomRight corner of two rectangles
    diff_X2 = abs(this_rect.aveMaxX - other_rect.aveMaxX)
    diff_Y2 = abs(this_rect.aveMaxY - other_rect.aveMaxY)

    dist1 = math.hypot(diff_X1, diff_Y1)
    dist2 = math.hypot(diff_X2, diff_Y2)

    if ((dist1 <= RADIUS) and (dist2 <= RADIUS)):
        return True
    else:
        return False

