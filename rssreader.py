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

sys.path.append("/home/pi/rpi-rgb-led-matrix/python/")
from rgbmatrix import RGBMatrix
from ledtxt import LedText
refreshRate = 60*5   # 5 minutes from now


config = json.load(open('config.json'))

ledtext = LedText(config['height'], config['panels']*32, '/home/pi/emojis', '/home/pi/two-sigma.png', "/home/pi/rpi-rgb-led-matrix/fonts/8x13.pil")

matrix = RGBMatrix(config['height'], config['panels'], 1)
matrix.pwmBits = 11
matrix.brightness = config['brightness']
double_buffer = matrix.CreateFrameCanvas()


txt = "STANDBY Alarm Clock"
im = ledtext.generate_image(txt)
img_width, img_height = im.size
xpos=-config['panels']*32

while True:
    stories = []
    for feed in config['feeds']:
        stories.extend(feedparser.parse(feed).entries)
    lastUpdate = time.time()

    #keep doing new stories until 
    while time.time() - lastUpdate < refreshRate:
        try:
            nxttxt = random.choice(stories).title
            nxtim = ledtext.generate_image(nxttxt + "  TwoSigma  ")
            nxtimg_width, nxtimg_height = nxtim.size
        except:
            continue
        while True:
            xpos += 3
            if (xpos > img_width):
                break

            double_buffer.SetImage(im, -xpos)
            double_buffer.SetImage(nxtim, -xpos + img_width)

            double_buffer = matrix.SwapOnVSync(double_buffer)
            time.sleep(0.15)
        xpos = 0
        im = nxtim
        img_width = nxtimg_width


