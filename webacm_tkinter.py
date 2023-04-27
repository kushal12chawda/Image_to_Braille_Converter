from __future__ import print_function
asciicodes = [' ','!','"','#','$','%','&','','(',')','*','+',',','-','.','/',
          '0','1','2','3','4','5','6','7','8','9',':',';','<','=','>','?','@',
          'a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q',
          'r','s','t','u','v','w','x','y','z','[','\\',']','^','_','\r','\n']

# Braille symbols
brailles = ['⠀','⠮','⠐','⠼','⠫','⠩','⠯','⠄','⠷','⠾','⠡','⠬','⠠','⠤','⠨','⠌','⠴','⠂','⠆','⠒','⠲','⠢',
        '⠖','⠶','⠦','⠔','⠱','⠰','⠣','⠿','⠜','⠹','⠈','⠁','⠃','⠉','⠙','⠑','⠋','⠛','⠓','⠊','⠚','⠅',
        '⠇','⠍','⠝','⠕','⠏','⠟','⠗','⠎','⠞','⠥','⠧','⠺','⠭','⠽','⠵','⠪','⠳','⠻','⠘','⠸',' ',' ']
brail_string=''

import datetime
import os
import threading
import tkinter as tki
import tkinter.messagebox as Messagebox
import requests
import io
import json
import cv2
import pytesseract as tess
import pyttsx3
from PIL import Image
from PIL import ImageTk

tess.pytesseract.tesseract_cmd = r"C:/Users/admin/AppData/Local/Tesseract-OCR/tesseract.exe"
# tess.pytesseract.tesseract_cmd = r"C:\Users\hp\appData\roaming\python\python311\site-packages\Tesseract-OCR\tesseract.exe"
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
print(voices[1].id)
engine.setProperty('voice', voices[0].id)
class PhotoBoothApp:
        global brail_string
        def __init__(self, vs, outputPath):
            # store the video stream object and output path, then initialize
            # the most recently read frame, thread for reading frames, and
            # the thread stop event
            self.vs = vs
            self.outputPath = outputPath
            self.frame = None
            self.thread = None
            self.stopEvent = None
            # initialize the root window and image panel
            self.root = tki.Tk()
            self.panel = None

            # create a button, that when pressed, will take the current
            # frame and save it to file
            btn = tki.Button(self.root, text="Snapshot!",
                             command=self.takeSnapshot)
            btn.pack(side="bottom", fill="both", expand="yes", padx=10,
                     pady=10)
            # start a thread that constantly pools the video sensor for
            # the most recently read frame
            self.stopEvent = threading.Event()
            self.thread = threading.Thread(target=self.videoLoop, args=())
            self.thread.start()
            # set a callback to handle when the window is closed
            self.root.wm_title("PhotoBooth")
            self.root.wm_protocol("WM_DELETE_WINDOW", self.onClose)


        def videoLoop(self):
            # DISCLAIMER:
            # I'm not a GUI developer, nor do I even pretend to be. This
            # try/except statement is a pretty ugly hack to get around
            # a RunTime error that Tkinter throws due to threading
            try:
                # keep looping over frames until we are instructed to stop
                while not self.stopEvent.is_set():
                    # grab the frame from the video stream and resize it to
                    # have a maximum width of 300 pixels
                    self.frame = self.vs.read()

                    # OpenCV represents images in BGR order; however PIL
                    # represents images in RGB order, so we need to swap
                    # the channels, then convert to PIL and ImageTk format
                    image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
                    image = Image.fromarray(image)
                    image = ImageTk.PhotoImage(image)

                    # if the panel is not None, we need to initialize it
                    if self.panel is None:
                        self.panel = tki.Label(image=image)
                        self.panel.image = image
                        self.panel.pack(side="left", padx=10, pady=10)

                    # otherwise, simply update the panel
                    else:
                        self.panel.configure(image=image)
                        self.panel.image = image

            except RuntimeError as e:
                    print("[INFO] caught a RuntimeError")


        def takeSnapshot(self):
            global brail_string
            brail_string=''
            # grab the current timestamp and use it to construct the
            # output path
            ts = datetime.datetime.now()
            filename = "{}.jpg".format(ts.strftime("%Y-%m-%d_%H-%M-%S"))
            p = os.path.sep.join((self.outputPath, filename))
            print(self.outputPath)
            # save the file
            cv2.imwrite(p, self.frame.copy())
            print("[INFO] saved {}".format(filename))
            img = cv2.imread(p)
            height, width, _ = img.shape

            # Cutting image
            # roi = img[0: height, 400: width]
            roi = img

            # Ocr
            url_api = "https://api.ocr.space/parse/image"
            _, compressedimage = cv2.imencode(".jpg", roi, [1, 90])
            file_bytes = io.BytesIO(compressedimage)
            result = requests.post(url_api,
                                   files={"screenshot.jpg": file_bytes},
                                   data={"apikey": "K81424530988957",
                                         "language": "eng"})

            result = result.content.decode()
            result = json.loads(result)
            parsed_results = result.get("ParsedResults")[0]
            text_detected = parsed_results.get("ParsedText")
            print(text_detected)
            text_detected=text_detected.replace('\r\n',' ')
            cv2.imshow("Img", img)
            engine.say(text_detected)
            engine.runAndWait()
            for element in text_detected:
                print(element, end=' ')
                data_match=element.lower()
                val = asciicodes.index(data_match)
                data = brailles[val]
                brail_string = brail_string + data
            print("\n")
            print(brail_string)
            file1 = open(f"{text_detected}.txt", "a+", encoding="utf-8")
            file1.writelines(text_detected)
            file1.write('\n')

            file1.write(brail_string)
            file1.write('\n')
            file1.close()  # to change file access modes

        def onClose(self):
            # set the stop event, cleanup the camera, and allow the rest of
            # the quit process to continue
            print("[INFO] closing...")
            self.stopEvent.set()
            self.vs.stop()
            self.root.quit()
