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
ledtext = LedText(config['panelheight']*config['chains'], config['panels']*32, '/home/pi/emojis', '/home/pi/two-sigma.png', "/home/pi/rpi-rgb-led-matrix/fonts/10x20.pil")

matrix = RGBMatrix(config['panelheight'], config['panels'], 2)
matrix.pwmBits = 11
matrix.brightness = config['brightness']
double_buffer = matrix.CreateFrameCanvas()

print("Input text")
inputtext = input()
im = ledtext.generate_image(inputtext)
img_width, img_height = im.size

xpos = 0
while True:
    xpos += 4
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
    time.sleep(0.1)


