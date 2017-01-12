import itertools
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
import select


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



ts = Image.open("/home/pi/two-sigma.png")
ts.resize([16, 16], Image.LANCZOS)


PREFIX = '/home/pi/emojis/'
HEIGHT = 16
FONTSIZE = 15

tsfn = '/home/pi/two-sigma.png'

#magic from http://stackoverflow.com/questions/6116978/python-replace-multiple-strings
emoji_res = {}
for cheat, uni in itertools.chain(emoji.unicode_codes.EMOJI_UNICODE.items(), emoji.unicode_codes.EMOJI_ALIAS_UNICODE.items()):
    try:
        emoji_res[re.compile(re.escape(cheat), re.IGNORECASE)] = uni
    except:
        print("broken as fuck", cheat, uni)
        raise
    try:
        emoji_res[re.compile("\\b"+re.escape(cheat.replace(":", "")).replace("-_", "[-_ ]")+"\\b", re.IGNORECASE)] = uni
    except:
        print("fancy shit broke", cheat, uni)
        raise
#emoji_re = re.compile("|".join(emoji_res.keys()), re.IGNORECASE)
#emoji_res = {re.compile(pattern, re.IGNORECASE): sub for pattern, sub in emoji_res.items()}

emojire = re.compile(r"""\\\\[Uu]0*([0-9a-f]{4,6})""")
tsre = re.compile(r"""Two ?Sigma(?: Investments| Advisors| Securities)?(?: LP| LLC)?""", re.IGNORECASE)

def generate_image(input_str):
    input_str = tsre.sub("TwoSigma", input_str)
    for pattern, replacement in emoji_res.items():
        input_str = pattern.sub(replacement, input_str)
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


sys.path.append("/home/pi/rpi-rgb-led-matrix/python/")
from rgbmatrix import RGBMatrix
matrix = RGBMatrix(16, 3, 1)
matrix.pwmBits = 11
matrix.brightness = 50
double_buffer = matrix.CreateFrameCanvas()


happy = "happy wave TwoSigma aversary 🎅 🍾 ⏰ 👨‍👨‍👦‍👦 🌮 👼🏿 amigo"
im = generate_image(happy)
img_width, img_height = im.size

xpos = 0
while True:
    xpos += 3
    if (xpos > img_width):
        xpos = 0 
    if select.select([sys.stdin,],[],[],0.0)[0]:
        txt = sys.stdin.readline()
        txt = emoji.emojize(txt, use_aliases=True)
        im = generate_image(txt)
        img_width, img_height = im.size
        xpos = 0

    double_buffer.SetImage(im, -xpos)
    double_buffer.SetImage(im, -xpos + img_width)

    double_buffer = matrix.SwapOnVSync(double_buffer)
    time.sleep(0.5)


