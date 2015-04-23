import SimpleCV
import cv2
import os
import time
import matplotlib.pyplot


class CharReader:

    def __init__(self, inp_image_path):

        char_template_list = []
        img_filename_list = os.listdir(inp_image_path)

        #Load all images and make CharTemplate objects
        for img_filename in img_filename_list:

            char_image = SimpleCV.Image(inp_image_path + img_filename)
            char_value = img_filename.split(".")[0].split("_")[0]

            this_char_template = CharTemplate(char_image, char_value)

            char_template_list.append(this_char_template)

        #Sort by value
        char_template_list.sort(key = lambda (this_template): this_template.value)

        #Store all CharTemplate objects
        self.templates = char_template_list


    def findMatch(self, inp_test_image, threshold=0, perform_unit_test=False):

        #Contains list of (char, percent) tuples.
        result_list = []

        for this_template in self.templates:
            template_image = this_template.image

            current_char = this_template.value
            perc_match = compareImage(inp_test_image, template_image)

            result_list.append((current_char, perc_match))

            #----------------------------------------------------------------
            if perform_unit_test:
                display = SimpleCV.Display((640, 480), title="SPEAR")

                print "Char:" + current_char + " [" + str(perc_match) + " %]"

                while not display.isDone():
                    w, h = inp_test_image.width, inp_test_image.height
                    inp_test_image.sideBySide(template_image.resize(w, h).invert()).save(display)

                    if display.mouseLeft:
                        display.done = True
                        time.sleep(0.2)
                display.done = False
            #---------------------------------------------------------------

        #Sort result_list by highest percentage
        result_list = sorted(result_list,
                             key=lambda(this_tuple): this_tuple[1],
                             reverse=True)

        #---------------------------------------------------------
        if perform_unit_test:

            match_plot = matplotlib.pyplot
            char_list, perc_list = [], []

            for pair in result_list:
                char_list.append(pair[0])
                perc_list.append(pair[1])

            match_plot.xticks(range(0, len(char_list)), char_list)
            match_plot.stem(perc_list)

            match_plot.show()
        #---------------------------------------------------------

        #If highest match is 0% then put a '?' Char instead
        if result_list[0][1] > float(threshold):
            best_match = result_list[0][0]
        else:
            best_match = '?'

        return best_match


class CharTemplate:

    def __init__(self, template_img, template_value):
        self.image = template_img
        self.value = template_value


def compareImage(test_image, template_image, compMeth=cv2.TM_SQDIFF_NORMED):
    """
    Method:
        Compares an image against a template and returns matching percentage.

    Parameters:
        test_image - A SimpleCV.Image to be used.
        template_image - A SimpleCV.Image for the template.
        compMeth = CV2 comparison method.

    Returns:
        Similarity percentage of two images.
    """

    #Resize template to fit test image
    template_image_cv2 = template_image.invert().resize(test_image.width, test_image.height).getGrayNumpyCv2()
    test_image_cv2 = test_image.getGrayNumpyCv2()

    match_result = cv2.matchTemplate(test_image_cv2, template_image_cv2, compMeth)
    match_percent = 100 - (100 * match_result[0][0])

    return match_percent


