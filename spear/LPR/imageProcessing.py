import subprocess
import SimpleCV
import cv2


def cropToROI(input_image,
              SIDE_MARGIN=(20.0, 80.0),
              TOP_BOTTOM_MARGIN=(20.0, 80.0)):

    """
    Method:
        Crops image to include only the
        Region of Interest (ROI)

    Parameters:
        input_image       - Image to crop.
        SIDE_MARGIN       - Tuple of margins on left and right sides (in percent).
        TOP_BOTTOM_MARGIN - Tuple of margines on top and bottom sides (in percent).

    Returns:
        A cropped SimpleCV.Image
    """
    width, height = input_image.width, input_image.height

    top_left = width * SIDE_MARGIN[0] / 100, height * TOP_BOTTOM_MARGIN[0] / 100
    bottom_right = width * SIDE_MARGIN[1] / 100, height * TOP_BOTTOM_MARGIN[1] / 100

    cropped_img = input_image.crop(top_left, bottom_right)

    return cropped_img


def equalize(input_image):

    """
    Method:
        Equalizes the Red, Green and Blue channels of an Image.

    Parameters:
        input_image - Image to be used.

    Returns:
        An equalized SimpleCV.Image
    """

    r, g, b = input_image.splitChannels()

    r_n = r.equalize()
    g_n = g.equalize()
    b_n = b.equalize()

    #r_n = r_n.normalize()
    #g_n = g_n.normalize()
    #b_n = b_n.normalize()

    equalized_img = input_image.mergeChannels(r_n, g_n, b_n)

    return equalized_img


def adaptiveEqualize(image, CLIP_LIMIT=2.0, GRID_SIZE=(8, 8)):

    r, g, b = image.splitChannels()

    ocv_r = r.getGrayNumpyCv2()
    ocv_g = g.getGrayNumpyCv2()
    ocv_b = b.getGrayNumpyCv2()

    clahe = cv2.createCLAHE(clipLimit=CLIP_LIMIT, tileGridSize=GRID_SIZE)

    scv_r = SimpleCV.Image(clahe.apply(ocv_r), cv2image=True)
    scv_g = SimpleCV.Image(clahe.apply(ocv_g), cv2image=True)
    scv_b = SimpleCV.Image(clahe.apply(ocv_b), cv2image=True)


    out_image = image.mergeChannels(scv_r, scv_g, scv_b)
    return out_image


def denoiseBilateralFilter(input_image, DELTA=30, SIGMA=20):

    """
    Method:
        Performs Bilateral Filter to remove Noise then MorphOpen

    Parameters:
        input_image - Image to be used.
        DELTA      - First parameter in Bilateral Filter.
        SIGMA      - Second parameter in Bilateral Filter.

    Returns:
        A denoised SimpleCV.Image
    """

    bf_img = input_image.bilateralFilter(DELTA, SIGMA)
    img = bf_img.morphOpen()

    return img
'''
def executeGMIC(input_image, gmic_command, gmic_arguments):

    buffer_directory = "gmicBuffer"
    inp_filename = buffer_directory + "/in.png"
    out_filename = buffer_directory + "/out.png"

    #Save an image first so that GMIC can use it.
    input_image.save(inp_filename)

    subprocess.call(["gmic", inp_filename, gmic_command, gmic_arguments, "-o", out_filename])

    #Load gmic's output as SimpleCV image
    output_image = SimpleCV.Image(out_filename)
    return output_image
'''
