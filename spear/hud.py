import cv2
import numpy
import platform
import plateRecog
import SimpleCV
import time
import socket
import databaseConstants as const

class SpearHUD:

    def __init__(self, hudPath, maskPath, scanHudPath, camResolution=(1920, 1080),
                 camIndex=1, displayResolution=(960, 540), windowName="SPEAR",
                 endKey='q', capKey='s', readKey='x', cannyKey='z',
                 incTH1='1', decTH1='!', incTH2='2', decTH2='@',
                 serverHost=None, serverPort=None,
                 savePath=None, dummyImagePath=None):

        #Load images to be used for HUD
        self.hudImage = cv2.imread(hudPath)
        self.maskImage = cv2.imread(maskPath)
        self.scanHudImage = cv2.imread(scanHudPath)

        self.camResolution = camResolution
        self.camIndex = camIndex

        self.displayResolution = displayResolution
        self.windowName = windowName

        self.endKey = endKey
        self.capKey = capKey
        self.readKey = readKey
        self.cannyKey = cannyKey
        self.incTH1 = incTH1
        self.decTH1 = decTH1
        self.incTH2 = incTH2
        self.decTH2 = decTH2

        self.serverHost = serverHost
        self.serverPort = serverPort

        #Saves images as it scans
        self.savePath = savePath

        #Use a static image as dummy camera output
        if dummyImagePath is not None:
            self.dummyImage = cv2.imread(dummyImagePath)
        else:
            self.dummyImage = None

        #System Information
        self.sysInfo = list(set(platform.uname()))
        self.sysInfo = filter(lambda (thisInfo): thisInfo != '', self.sysInfo)
        self.sysInfo = filter(lambda (thisInfo): len(thisInfo) < 40, self.sysInfo)
        self.sysInfo.reverse()


    def run(self):

        #Prepare Camera and Window
        self.cam = cv2.VideoCapture(self.camIndex)
        self.cam.set(3, self.camResolution[0]) #Width
        self.cam.set(4, self.camResolution[1]) #Height

        cv2.namedWindow(self.windowName, cv2.WINDOW_OPENGL)
        cv2.resizeWindow(self.windowName, self.displayResolution[0], self.displayResolution[1])

        #Connect to SPEAR Server if given an IP and a PORT
        if self.serverHost and self.serverPort:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            try:
                client_socket.connect((self.serverHost, self.serverPort))
                self.clientSocket = client_socket
                self.clientHost, self.clientPort = self.clientSocket.getsockname()
            except socket.error:
                print "Unable to connect to %s:%i" %(self.serverHost, self.serverPort)
                self.connected = None

        else:
            self.clientSocket = None

        self._showHUD()


    def _showHUD(self):

        #Initial Value for Recognition and Assessment
        alpha_code_list = ['------']
        assessment_list = ['N/A']

        #For visual feedback
        rect_list = None
        visual_timeout = 3

        #Capture and Show Image
        while True:
            __, stream_img = self.cam.read()

            #Overwrite camera output if have dummy image
            if self.dummyImage is not None:
                stream_img = self.dummyImage.copy()

            #Keybindings
            k = cv2.waitKey(1) & 0xFF

            if k == ord(self.endKey):
                break

            if k == ord(self.capKey):
                cv2.imwrite(time.ctime() + ".jpg", stream_img)

            if k == ord(self.readKey):
                #Make independent copy of image
                image_to_scan = stream_img.copy()

                #Draw Standby HUD
                _drawSemiTransparentBackground(stream_img, (384,1536), (216,864))
                cv2.multiply(stream_img, self.maskImage, stream_img)
                cv2.add(stream_img, self.scanHudImage, stream_img)
                cv2.imshow(self.windowName, stream_img)
                cv2.waitKey(1)

                #Perform LPR
                alpha_code_list, rect_list = _scanImage(image_to_scan)
                if rect_list:
                    time_appeared = time.time()

                #Query to SPEAR Server if connected and got a valid alpha_code_list
                if (self.clientSocket) and (alpha_code_list != ['------']):
                    to_send = ''.join(alpha_code_list)
                    self.clientSocket.sendall(to_send)
                    to_recv = int(self.clientSocket.recv(2048).strip('\n'))
                    assessment_list = const.interpretCode(to_recv)
                else:
                    assessment_list = ['N/A']

                #Save image if given a testPath
                if self.savePath:
                    filename = "%s/%s_[%s].jpg" %(self.savePath, time.ctime()[11:19], ','.join(alpha_code_list))
                    cv2.imwrite(filename, image_to_scan)

            #Make a cropped copy of ROI
            cropped_img = stream_img[216:864, 384:1536].copy()

            #Draw semitransparent background to see HUD better
            _drawSemiTransparentBackground(stream_img, (1568, 1883), (216, 522))
            _drawSemiTransparentBackground(stream_img, (1568, 1883), (558, 864))
            _drawSemiTransparentBackground(stream_img, (162, 260), (215, 865))
            _drawSemiTransparentBackground(stream_img, (384,1536), (216,864))

            #Apply Mask then HUD
            cv2.multiply(stream_img, self.maskImage, stream_img)
            cv2.add(stream_img, self.hudImage, stream_img)

            #Draw Triangle pointer for Light Level
            ave = int(cropped_img.mean() * float(648) / 255)
            pt1 = (165, 864-ave-20)
            pt2 = (185, 864-ave)
            pt3 = (165, 864-ave+20)

            cv2.line(stream_img, pt1, pt2, (0, 255, 0), 2)
            cv2.line(stream_img, pt2, pt3, (0, 255, 0), 2)
            cv2.line(stream_img, pt1, pt3, (0, 255, 0), 2)

            #Draw Rectangle if found Characters
            if rect_list:
                for top_left, bottom_right in rect_list:
                    cv2.rectangle(stream_img, top_left, bottom_right, (0, 255, 0), 2)

                if (time.time() - time_appeared) >= visual_timeout:
                    rect_list = None

            #Print Text Data
            _printListedText(stream_img, "SYSTEM INFO", self.sysInfo, (1585, 255))
            _printListedText(stream_img, "PLATE RECOGNITION", alpha_code_list, (1585, 615),
                             text_scale_factor=1, header_list_spacing=20)
            _printListedText(stream_img, "PLATE ASSESSMENT", assessment_list, (1585, 720))

            if self.clientSocket:
                connection = ["[Client] %s:%i" %(self.clientHost, self.clientPort),
                              "[Server] %s:%i" %(self.serverHost, self.serverPort)]
            else:
                connection = ['N/A']
            _printListedText(stream_img, "CONNECTION", connection, (1585, 430))

            #Update display
            cv2.imshow(self.windowName, stream_img)

        #Clean up
        cv2.destroyWindow(self.windowName)
        self.cam.release()

        if self.clientSocket:
            self.clientSocket.close()


def _scanImage(opencv_img):

    img_SCV = SimpleCV.Image(opencv_img, cv2image=True)

    result = plateRecog.scanImage(img_SCV)

    if result:
        char_val_list, rect_list = result
        alphaNumCode = ''.join(char_val_list)

        return [alphaNumCode], rect_list

    else:
        return ["------"], None


def _drawSemiTransparentBackground(image, (x1, x2), (y1, y2), alpha1=0.4, alpha2=0.6, gamma=0):
            window = image[y1:y2, x1:x2]
            window_bg = numpy.zeros(window.shape, numpy.uint8)

            image[y1:y2, x1:x2] = cv2.addWeighted(window, alpha1, window_bg, alpha2, gamma)


def _printListedText(image, header_text, text_list, top_left,
                    font=cv2.FONT_HERSHEY_SIMPLEX, head_scale_factor=0.7,
                    text_scale_factor=0.6, text_color=(0, 255, 0), text_weight=2,
                    list_indent=15, header_list_spacing=10, break_spacing=30):
    x, y = top_left

    cv2.putText(image, header_text, top_left, font, head_scale_factor, text_color, text_weight)

    for index, text in enumerate(text_list):
        x_text = x + list_indent
        y_text = y + header_list_spacing + ((index+1) * 30)

        cv2.putText(image, text, (x_text, y_text), font, text_scale_factor, text_color, text_weight)
