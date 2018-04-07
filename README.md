## Basic Setup:

Upon boot run raspi-config. Set the hostname, expand the FS if it didn't do it,
enable ssh, change the password, change the locale and keyboard, etc.

Add wifi: https://www.raspberrypi.org/documentation/configuration/wireless/wireless-cli.md

	network={
	    ssid="The_ESSID_from_earlier"
	    psk="Your_wifi_password"
	    priority=5
	}

You may want to setup a nicer bashrc history (if you don't have one handy):

	HISTSIZE=10000
	HISTFILESIZE=20000
	shopt -s histappend                      # append to history, don't overwrite it
	
	# Save and reload the history after each command finishes
	PROMPT_COMMAND="history -a; history -c; history -r; $PROMPT_COMMAND"

Or vimrc:

	syntax on
	set nu
	set nocompatible

Disable sound:

	cat <<EOF | sudo tee /etc/modprobe.d/blacklist-rgb-matrix.conf
	blacklist snd_bcm2835
	EOF
	sudo update-initramfs -u
	sudo reboot

Install packages. technically cython3 and python3-numpy shouldn't be required unless,
you want to rebuild the cpp source code, and want fast SetImage implementation

	sudo apt-get update
	sudo apt-get install python3 python3-dev python3-pip python3-numpy git vim  -y
	sudo apt-get install  zlibc  libjpeg-dev libfreetype6-dev libtiff5-dev libwebp-dev libopenjpeg-dev  -y
	sudo pip3 install emoji Feedparser cython Pillow 

## Prepare Emoji pngs

On a current/recent mac, fetch [gemoji](https://github.com/github/gemoji/) and run:
	
	bundle exec gemoji extract public/images/emoji --size=32

Then transfer the public/images/emoji/unicode directory to the pi. 


## Make the code

`cd` to the rpi-rgb-led-matrix/python directory and run

	make build-python PYTHON=$(which python3) CYTHON=$(which cython3)
	sudo make install-python PYTHON=$(which python3) CYTHON=$(which cython3)

> pi@chrismpi3:~/rpi-rgb-led-matrix/examples-api-use $ time sudo ./benchmark -r 16 -c 2 -b 25 runtext16.ppm 
> Size: 64x16. Hardware gpio mapping: adafruit-hat
> Read image 'runtext16.ppm' with 281x16
> Press <CTRL-C> to exit and reset LEDs
>
> real	1m1.827s
> user	0m32.270s
> sys	0m3.040s
> pi@chrismpi3:~/rpi-rgb-led-matrix/examples-api-use $ cd ../python/samples/
> pi@chrismpi3:~/rpi-rgb-led-matrix/python/samples $ vim benchmark.cc ^C
> pi@chrismpi3:~/rpi-rgb-led-matrix/python/samples $ rpython^C
> pi@chrismpi3:~/rpi-rgb-led-matrix/python/samples $ time sudo python3 benchmark.py -r 16 -c 2 -b 25
> Press CTRL-C to stop sample
> slow:  2.384185791015625e-08
> fast:  0.6199548578262329
> 
> real	1m2.836s
> user	0m35.860s
> sys	0m2.780s
> pi@chrismpi3:~/rpi-rgb-led-matrix/python/samples $ make^C
> pi@chrismpi3:~/rpi-rgb-led-matrix/python/samples $ vim benchmark.py 
> pi@chrismpi3:~/rpi-rgb-led-matrix/python/samples $ time sudo python3 benchmark.py -r 16 -c 2 -b 25 #this is the slow one
> Press CTRL-C to stop sample
> slow:  1.2335465025901795
> fast:  2.384185791015625e-08
> 
> real	2m4.169s
> user	1m56.160s
> sys	0m5.440s
