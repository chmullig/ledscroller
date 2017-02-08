import feedparser
import os.path
import os
import sys
import re
import time
import select
import json

sys.path.append("/home/pi/rpi-rgb-led-matrix/python/")
from rgbmatrix import RGBMatrix
from ledtxt import LedText



config = json.load(open('config.json'))

ledtext = LedText(config['height'], config['panels']*32, '/home/pi/emojis', '/home/pi/two-sigma.png', "/home/pi/rpi-rgb-led-matrix/fonts/8x13.pil")

matrix = RGBMatrix(config['height'], config['panels'], 1)
matrix.pwmBits = 11
matrix.brightness = config['brightness']
double_buffer = matrix.CreateFrameCanvas()


happy = "Alarm Clock"
im = ledtext.generate_image(happy)
img_width, img_height = im.size

xpos = 0
while True:
    xpos += 3
    if (xpos > img_width):
        xpos = 0 
    if select.select([sys.stdin,],[],[],0.0)[0]:
        txt = sys.stdin.readline()
        im = ledtext.generate_image(txt)
        img_width, img_height = im.size
        xpos = 0

    double_buffer.SetImage(im, -xpos)
    double_buffer.SetImage(im, -xpos + img_width)

    double_buffer = matrix.SwapOnVSync(double_buffer)
    time.sleep(0.5)


