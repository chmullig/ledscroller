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
import requests
import collections

sys.path.append("/home/pi/rpi-rgb-led-matrix/python/")
from rgbmatrix import RGBMatrix
from ledtxt import LedText
refreshRate = 30   # 30 seconds from now


config = json.load(open('config.json'))

ledtext = LedText(config['panelheight']*config['chains'], config['panelwidth']*config['panels'], '/home/pi/emojis', '/home/pi/two-sigma.png', "/home/pi/ledscroller/fonts/MTA.ttf")

matrix = RGBMatrix(config['panelheight'], config['panels'], config['chains'])
matrix.pwmBits = 11
matrix.brightness = config['brightness']
double_buffer = matrix.CreateFrameCanvas()

txt = "Two Sigma Alarm Clock "
import socket
try:
    #from https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
    ip = [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]
    txt += "".join(ip)
except:
    pass

print(txt)
im = ledtext.generate_image(txt, pad_top=6)
img_width, img_height = im.size
xpos=0
double_buffer.SetImage(im, -xpos)
double_buffer = matrix.SwapOnVSync(double_buffer)

stories = set()
storiesLock = threading.Lock()

class FeedFetcher(threading.Thread):
    def run(self):
        while True:
            try:
                status = requests.get("http://localhost:23432/rest/status", timeout=30)
                arrivals = requests.get("http://localhost:23432/rest/arrivals?station=Canal%20St&line=1&line=A&line=C&line=E&line=6&line=J&line=N&line=Q&line=R&line=Z", timeout=30)
            except requests.exceptions.Timeout:
                time.sleep(100)
                continue

            statuses = status.json()
            messages = collections.defaultdict(set) #message: lines
            for line, status in statuses['results'].items():
                for mtype in ['service change', 'delays']:
                    try:
                        message = status[mtype]
                        messages[message].add(line)
                    except KeyError:
                        pass
#            nextTrains = arrivals.json()
#            for line in nextTrains.keys():
#                upcomingTrains = sorted(line['arrivals'], key=lambda x: x.get('projectedArrivalTime', x.get('scheduledArrivalTime', 2000000000000)))
#                for train in upcomingTrains:
#                    pass


            storiesLock.acquire()
            while stories:
                stories.pop()
            for status, lines in messages.items():
                stories.add("{}: {}".format("/".join(sorted(list(lines))), status))
            if not messages:
                stories.add("All seem to be running OK")
            print(stories)
            storiesLock.release()
            print("Stories added")
            time.sleep(refreshRate)

feedfetcher = FeedFetcher()
feedfetcher.start()

images = queue.Queue(5)
class ImageMaker(threading.Thread):
    def run(self):
        while True:
            try:
                storiesLock.acquire()
                if not stories:
                    storiesLock.release()
                    time.sleep(5)
                    continue
                selection = random.choice(tuple(stories))
                storiesLock.release()
                nxttxt = selection
                nxtim = ledtext.generate_image(nxttxt + "  TwoSigma  ", pad_top=6)
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
                time.sleep(0.09)
                break

            double_buffer.SetImage(im, -xpos)
            double_buffer.SetImage(nxtim, -xpos + img_width)

            double_buffer = matrix.SwapOnVSync(double_buffer)
            time.sleep(0.25)
        xpos = 0
        im = nxtim
        img_width = nxtimg_width
    except:
        raise


