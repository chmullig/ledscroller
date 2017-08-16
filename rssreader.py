import feedparser
import os.path
import os
import sys
import re
import time
import select
import json
import random
import time
import threading
import queue

sys.path.append("/home/pi/rpi-rgb-led-matrix/python/")
from rgbmatrix import RGBMatrix
from ledtxt import LedText
refreshRate = 60*5   # 5 minutes from now


config = json.load(open('config.json'))

ledtext = LedText(config['panelheight']*config['chains'], config['panelwidth']*config['panels'], '/home/pi/emojis', '/home/pi/two-sigma.png', "/home/pi/rpi-rgb-led-matrix/fonts/10x20.pil")

matrix = RGBMatrix(config['panelheight'], config['panels'], config['chains'])
matrix.pwmBits = 11
matrix.brightness = config['brightness']
double_buffer = matrix.CreateFrameCanvas()


txt = " Two Sigma  STANDBY Alarm Clock"
im = ledtext.generate_image(txt)
img_width, img_height = im.size
xpos=0
double_buffer.SetImage(im, -xpos)
double_buffer = matrix.SwapOnVSync(double_buffer)

stories = set()
storiesLock = threading.Lock()

class FeedFetcher(threading.Thread):
    def run(self):
        for feed in config['feeds']:
            fetched = feedparser.parse(feed).entries
            storiesLock.acquire()
            stories.update(fetched)
            storiesLock.release()
            print("Stories added")
            time.sleep(refreshRate / len(config['feeds']))

feedfetcher = FeedFetcher()
feedfetcher.start()

images = queue.Queue(5)
class ImageMaker(threading.Thread):
    def run(self):
        while True:
            try:
                if not stories:
                    continue
                print("ok going to grab a random story")
                storiesLock.acquire()
                selection = random.choice(tuple(stories))
                storiesLock.release()
                nxttxt = selection.title
                nxtim = ledtext.generate_image(nxttxt + "  TwoSigma  ")
                print("trying to put an image")
                images.put(nxtim)
                print("image put")
            except Exception as e:
                print(e)
            time.sleep(1)

imagemaker = ImageMaker()
imagemaker.start()

while True:
    try:
        print("Trying to get an image")
        nxtim = images.get()
        nxtimg_width = nxtim.size[0]
        while True:
            xpos += 2
            if (xpos > img_width):
                break

            double_buffer.SetImage(im, -xpos)
            double_buffer.SetImage(nxtim, -xpos + img_width)

            double_buffer = matrix.SwapOnVSync(double_buffer)
            time.sleep(0.1)
        xpos = 0
        im = nxtim
        img_width = nxtimg_width
    except:
        raise


