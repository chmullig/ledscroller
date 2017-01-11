
# coding: utf-8

# In[1]:

import feedparser
import PIL
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 
import os.path
import emoji
import os
import sys
import numpy as np
import re
import time




def alpha_composite(front, back):
    """Alpha composite two RGBA images.

    Source: http://stackoverflow.com/a/9166671/284318
    and http://stackoverflow.com/questions/9166400/convert-rgba-png-to-rgb-with-pil

    Keyword Arguments:
    front -- PIL RGBA Image object
    back -- PIL RGBA Image object

    """
    front = np.asarray(front)
    back = np.asarray(back)
    result = np.empty(front.shape, dtype='float')
    alpha = np.index_exp[:, :, 3:]
    rgb = np.index_exp[:, :, :3]
    falpha = front[alpha] / 255.0
    balpha = back[alpha] / 255.0
    result[alpha] = falpha + balpha * (1 - falpha)
    old_setting = np.seterr(invalid='ignore')
    result[rgb] = (front[rgb] * falpha + back[rgb] * balpha * (1 - falpha)) / result[alpha]
    np.seterr(**old_setting)
    result[alpha] *= 255
    np.clip(result, 0, 255)
    # astype('uint8') maps np.nan and np.inf to 0
    result = result.astype('uint8')
    result = Image.fromarray(result, 'RGBA')
    return result


def alpha_composite_with_color(image, color=(255, 255, 255)):
    """Alpha composite an RGBA image with a single color image of the
    specified color and the same size as the original image.

    Keyword Arguments:
    image -- PIL RGBA Image object
    color -- Tuple r, g, b (default 255, 255, 255)

    """
    back = Image.new('RGBA', size=image.size, color=color + (255,))
    return alpha_composite(image.convert("RGBA"), back).convert("RGB")


# In[2]:

feedparser.parse("http://feeds.reuters.com/reuters/topNews")


# In[3]:

ts = Image.open("/home/pi/two-sigma.png")
ts.resize([16, 16], Image.LANCZOS)


# In[4]:

PREFIX = '/home/pi/emojis/'
HEIGHT = 16
FONTSIZE = 15

tsfn = '/home/pi/two-sigma.png'


emojire = re.compile(r"""\\\\[Uu]0*([0-9a-f]{4,6})""")


happy = "happy TwoSigma aversary 🎅 🍾 ⏰ 👨‍👨‍👦‍👦 🌮 👼🏿 amigo"

def generate_image(input_str):
    input_str = input_str.split()
    im = Image.new('RGB', (1024,16))
    draw = ImageDraw.Draw(im)
    draw = ImageDraw.Draw(im)
    font = ImageFont.load("/home/pi/rpi-rgb-led-matrix/fonts/9x"+str(FONTSIZE)+".pil")
    offset = 0
    last = None
    for text in input_str:
        if text == 'TwoSigma':
            tspng = Image.open(tsfn)
            tspng = alpha_composite_with_color(tspng, (0,0,0))
            tspng = tspng.resize((HEIGHT, HEIGHT), PIL.Image.LANCZOS)
            im.paste(tspng, (offset, 0))
            offset += 16
            last = 'logo'
        elif any(text.startswith(x) for x in emoji.UNICODE_EMOJI.keys()):
            codepoints = emojire.findall(str(text.encode("unicode_escape")))
            print(codepoints)
            codepoints = [x for x in codepoints if x != '200d']
            try:
                fn = os.path.join(PREFIX, "-".join(codepoints) + '.png')
                emojipng = Image.open(fn)
            except FileNotFoundError:
                fn = os.path.join(PREFIX, codepoints[0] + '.png')
                emojipng = Image.open(fn)
            emojipng = alpha_composite_with_color(emojipng, (0,0,0))
            emojipng = emojipng.resize((HEIGHT, HEIGHT), PIL.Image.LANCZOS)
            im.paste(emojipng, (offset, 0))
            offset += 16
            last = 'emoji'
        else:
            text = (" " if last in ['emoji', 'logo'] else "") + text + " "
            draw.text((offset, 0), text, (255,255,255), font=font)
            offset += draw.textsize(text, font=font)[0]
    im = im.crop((0,0,offset,HEIGHT))
    return im

print("importing")
sys.path.append("/home/pi/rpi-rgb-led-matrix/python/")
from rgbmatrix import RGBMatrix

print("imported")
matrix = RGBMatrix(16, 2, 1)
matrix.pwmBits = 11
matrix.brightness = 25

print("initialized")
double_buffer = matrix.CreateFrameCanvas()


print("let's scroll")
# let's scroll
xpos = 0

im = generate_image(happy)
img_width, img_height = im.size
import select

while True:
    xpos += 3
    if (xpos > img_width):
        xpos = 0 
    if select.select([sys.stdin,],[],[],0.0)[0]:
        im = generate_image(sys.stdin.readline())
        img_width, img_height = im.size
        xpos = 0

    double_buffer.SetImage(im, -xpos)
    double_buffer.SetImage(im, -xpos + img_width)

    double_buffer = matrix.SwapOnVSync(double_buffer)
    time.sleep(0.5)


