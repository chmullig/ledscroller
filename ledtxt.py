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

class LedText:
    def __init__(self, height, width, emojis_path, tsfn, font_path):
        self.height = height
        self.width = width
        self.font_path = font_path
        #"/home/pi/rpi-rgb-led-matrix/fonts/9x"+str(FONTSIZE)+".pil"
        self.font = ImageFont.load(font_path)

        self.tsfn = tsfn
        self.tspng = Image.open(tsfn)
        self.tspng = alpha_composite_with_color(self.tspng, (0,0,0))
        self.tspng = self.tspng.resize([self.height, self.height], Image.LANCZOS)
        self.tsre = re.compile(r"""Two ?Sigma(?: Investments| Advisors| Securities)?(?: LP| LLC)?""", re.IGNORECASE)

        self.emojis_path = emojis_path
        #magic from http://stackoverflow.com/questions/6116978/python-replace-multiple-strings
        self.emoji_res = {}
        for cheat, uni in itertools.chain(emoji.unicode_codes.EMOJI_UNICODE.items(), emoji.unicode_codes.EMOJI_ALIAS_UNICODE.items()):
            try:
                self.emoji_res[re.compile(re.escape(cheat), re.IGNORECASE)] = uni
            except:
                print("broken as fuck", cheat, uni)
            try:
                self.emoji_res[re.compile("\\b"+cheat.replace(":", "").replace("-", "[-_ ]").replace("_", "[-_ ]")+"\\b", re.IGNORECASE)] = uni
            except:
                print("fancy shit broke", cheat, uni)
            if cheat.startswith(":flag_for_"):
                cheat = cheat.replace(":", "").replace("flag_for_", "")
                self.emoji_res[re.compile("\\b"+cheat.replace("-", "[-_ ]").replace("_", "[-_ ]")+"\\b", re.IGNORECASE)] = uni
        self.codepointre = re.compile(r"""\\\\[Uu]0*([0-9a-f]{3,7})""")

    def generate_image(self, input_str, emoji_replace=True):
        if emoji_replace:
            input_str = self.tsre.sub("TwoSigma", input_str)
            #input_str = emoji.emojize(input_str)
            #input_str = emoji.emojize(input_str, use_aliases=True)
            for pattern, replacement in self.emoji_res.items():
                input_str = pattern.sub(replacement, input_str)
        im = Image.new('RGB', (self.width*100, self.height))
        draw = ImageDraw.Draw(im)
        offset = 0
        last = None
        input_list = re.findall(r"\w+|\W+", input_str)
        print(input_list)
        for text in input_list:
            if emoji_replace and 'TwoSigma' in text:
                im.paste(self.tspng, (offset, 0))
                offset += self.height
                last = 'logo'
            elif emoji_replace and any(x in text for x in emoji.UNICODE_EMOJI.keys()):
                codepoints = self.codepointre.findall(str(text.encode("unicode_escape")))
                codepoints = [x for x in codepoints if x != '200d']
                try:
                    fn = os.path.join(self.emojis_path, "-".join(codepoints) + '.png')
                    emojipng = Image.open(fn)
                except FileNotFoundError:
                    fn = os.path.join(self.emojis_path, codepoints[0] + '.png')
                    emojipng = Image.open(fn)
                emojipng = alpha_composite_with_color(emojipng, (0,0,0))
                if emojipng.size[0] > self.height:
                    emojipng = emojipng.resize((self.height, self.height), PIL.Image.LANCZOS)
                im.paste(emojipng, (offset, 0))
                offset += self.height
                last = 'emoji'
            else:
                draw.text((offset, 0), text, (255,255,255), font=self.font)
                offset += draw.textsize(text, font=self.font)[0]
        im = im.crop((0,0,max(offset, self.width), self.height))
        return im


