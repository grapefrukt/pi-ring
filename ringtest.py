import colorsys
import math
from neopixel import *
import netinfo
import os
from pysnmp.hlapi import *
import random
import threading
import time

# LED strip configuration:
LED_COUNT      = 24      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)

BW_SAMPLES     = 5       # Number of bandwidth samples to keep
BW_FREQUENCY   = 2       # Delay in seconds between polls of bandwidth data

GAMMA          = .6
MAX_BRIGHTNESS = .85

def clamp(val, minval, maxval):
    return max(min(val, maxval), minval)
    
def gamma(original) :
    return math.pow((original), (1.0 / GAMMA))
    
def convert(input) :
    return int(gamma(input) * MAX_BRIGHTNESS * 0xff)

# Define functions which animate LEDs in various ways.
def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/1000.0)

class GetDataBackground(threading.Thread):
   def run(self):
      while 1 :
        # get the time before we query the router
        t = time.time()
        GetData()
        # figure out how long that took
        delta = time.time() - t
        # if it took longer than our preferred frequency, something went wrong
        # reset the delta and hope for better luck next time
        if delta > BW_FREQUENCY : delta = 0
        # finally, sleep until its time to update the values again
        time.sleep(BW_FREQUENCY - delta)


def GetData():
    global router_ip
    cmd = getCmd(SnmpEngine(),
         CommunityData('public', mpModel=1),
         UdpTransportTarget((router_ip, 161)),
         ContextData(),
         ObjectType(ObjectIdentity('IF-MIB', 'ifHCInOctets', 2)),
         ObjectType(ObjectIdentity('IF-MIB', 'ifHCOutOctets', 2)))

    errorIndication, errorStatus, errorIndex, varBinds = next(cmd)

    if errorIndication:
        print(errorIndication)
    elif errorStatus:
        print('%s at %s' % (errorStatus.prettyPrint(),
            errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
    else:
        #print('snmp response')
        global rx
        global rx_delta
        global tx
        global tx_delta

        rx_new = float(varBinds[0][1] / 1024 / 1024)
        tx_new = float(varBinds[1][1] / 1024 / 1024)

        rx_delta = rx_new - rx
        #rx_delta = random.randint(0, 70)
        tx_delta = tx_new - tx

        if rx == 0 : rx_delta = 0
        if tx == 0 : tx_delta = 0

        rx = rx_new
        tx = tx_new

        #print("rx:            " + str(rx))
        #print("rx_delta:      " + str(rx_delta))
        #print("")

# Main program logic follows:
if __name__ == '__main__':
    # timestep size (in seconds)
    t = .05
    wipetime = t * .5 * 1000
    
    # sets the process to run at a higher priority
    os.nice(-10)
    
    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
    # Intialize the library (must be called once before other functions).
    strip.begin()

    colorWipe(strip, Color(0, 64, 0), wipetime)

    tx = 0.0
    tx_delta = 0.0
    rx = 0.0
    rx_delta = 0.0

    router_ip = ''
    for route in netinfo.get_routes() :
        if route['dest'] == '0.0.0.0' : router_ip = route['gateway']

    print 'router is at ' + router_ip

    colorWipe(strip, Color(64, 0, 0), wipetime)

    thread = GetDataBackground()
    thread.daemon = True
    thread.start()

    i = 0
    while rx == 0 or i % 2 == 1:
        i = i + 1
        if i % 2 == 1 :
            colorWipe(strip, Color(0, 0, 64), wipetime)
        else :
            colorWipe(strip, Color(0, 0, 0), wipetime)

    spin_speed = 0.0
    spin = 0.0

    while True:

        scaled = rx_delta / 10.0
        if spin_speed < scaled : spin_speed = spin_speed + (scaled - spin_speed) * .30 * t
        if spin_speed > scaled : spin_speed = spin_speed + (scaled - spin_speed) * .20 * t
        if spin_speed < 0 : spin_speed = 0

        spin = spin + spin_speed

        # vary brightness to keep things moving when no traffic
        brightness = math.sin(time.time() * 1.3) / 2.0 + .5 + spin_speed * .5
        # set a minimum brightness above zero
        brightness = brightness * .9 + .1
        # set the maximum brightness, will go as low as .004
        brightness = clamp(brightness, 0, 1)

        for i in range(strip.numPixels()) :
            dist = math.sin((i - spin) / 24.0 * 3.1416 * 2.0) / 2.0 + .5
            dist = dist * 4 - 3
            dist = clamp(dist, 0, 1)
            dist = dist * dist * dist * dist * dist

            rgb = colorsys.hsv_to_rgb(abs((spin+i) / 240.0) % 1.0, 1.0, clamp(dist, 0, brightness))
            strip.setPixelColorRGB(i, int(rgb[1] * 0xff), int(rgb[0] * 0xff), int(rgb[2] * 0xff))

        strip.show()
        time.sleep(t)
