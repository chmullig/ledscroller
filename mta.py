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

lineSymbolLookup = {
    1 : "!",
    2 : "@",
    3 : "#",
    4 : "$",
    5 : "%",
    6 : "^",
}
for k, v in list(lineSymbolLookup.items()):
    lineSymbolLookup[str(k)] = v

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

statusMessages = set()
trainsToShow = {}
statusMessagesLock = threading.Lock()

class FeedFetcher(threading.Thread):
    def run(self):
        while True:
            try:
                status = requests.get("http://localhost:23432/rest/status", timeout=10)
                arrivals = requests.get("http://localhost:23432/rest/arrivals?station=Canal%20St&line=1&line=A&line=C&line=E&line=6&line=J&line=N&line=Q&line=R&line=Z", timeout=10)
            except requests.exceptions.Timeout:
                time.sleep(500)
                continue

            statuses = status.json()
            print("statuses", statuses)
            messages = collections.defaultdict(set) #message: lines
            for line, status in statuses['results'].items():
                for mtype in ['service change', 'delays']:
                    try:
                        message = status[mtype].title()
                        messages[message].add(line)
                    except KeyError:
                        pass
            print("messages:", messages)

            nextTrains = arrivals.json()

            statusMessagesLock.acquire()
            trainsToShow.clear()
            for line, lineDetails in nextTrains.items():
                upcomingTrains = sorted(lineDetails['arrivals'], key=lambda x: int(x.get('projectedArrivalTime', x.get('scheduledArrivalTime', 0))))
                for train in upcomingTrains:
                    key = (line, train['headsign'])
                    train['line'] = line
                    if key not in trainsToShow:
                        trainsToShow[key] = train
            while statusMessages:
                statusMessages.pop()
            for status, lines in messages.items():
                statusMessages.add("{}: {}".format("/".join(sorted(list(lines))), status))
            if not messages:
                statusMessages.add("All seem to be running OK")
            print(statusMessages)
            statusMessagesLock.release()
            print("Stories added")
            time.sleep(refreshRate)

feedfetcher = FeedFetcher()
feedfetcher.start()

images = queue.Queue(5)
class ImageMaker(threading.Thread):
    def run(self):
        while True:
            try:
                statusMessagesLock.acquire()
                for message in statusMessages:
                    selection = random.choice(tuple(statusMessages))
                    nxtim = ledtext.generate_image(selection + "  TwoSigma  ", pad_top=6)
                    images.put(nxtim)
                for _, train in trainsToShow.items():
                    atime = train.get('projectedArrivalTime', train['scheduledArrivalTime']) / 1000.0
                    print(atime)
                    now = time.time() 
                    print(now)
                    eta = (atime - now) / 60
                    print(eta)
                    lineSymbol = lineSymbolLookup.get(train['line'], "(%s)" % train['line'])
                    arrivalLine = "{line} {headsign} {eta:.6f}min".format(eta=eta, line=lineSymbol, headsign=train['headsign'].title())
                    nxtim = ledtext.generate_image(arrivalLine + "  TwoSigma  ", pad_top=6)
                    images.put(nxtim)
                statusMessagesLock.release()
                time.sleep(5)
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
            xpos += 1 
            if (xpos > img_width):
                time.sleep(0.09)
                break

            double_buffer.SetImage(im, -xpos)
            double_buffer.SetImage(nxtim, -xpos + img_width)

            double_buffer = matrix.SwapOnVSync(double_buffer)
            time.sleep(0.05)
        xpos = 0
        im = nxtim
        img_width = nxtimg_width
    except:
        raise


