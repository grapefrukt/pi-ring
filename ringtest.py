import math
from neopixel import *
import netinfo
from pysnmp.hlapi import *
import random
import threading
import time

router_ip = ''
for route in netinfo.get_routes() :
    if route['dest'] == '0.0.0.0' :
	router_ip = route['gateway']

print 'router is at ' + router_ip

# LED strip configuration:
LED_COUNT      = 24      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)

BW_SAMPLES     = 5       # Number of bandwidth samples to keep
BW_FREQUENCY   = 2       # Delay in seconds between polls of bandwidth data

def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)

tx = 0.0
tx_delta = 0.0
rx = 0.0
rx_delta = 0.0

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
        print('snmp response')
        global rx
        global rx_delta
        global tx
        global tx_delta

        rx_new = float(varBinds[0][1] / 1024 / 1024)
        tx_new = float(varBinds[1][1] / 1024 / 1024)

        #rx_delta = rx_new - rx
        rx_delta = random.randint(0, 70)
        tx_delta = tx_new - tx

        if rx == 0 : rx_delta = 0
        if tx == 0 : tx_delta = 0

        rx = rx_new
        tx = tx_new

        print("rx:            " + str(rx))
        print("rx_delta:      " + str(rx_delta))
        print("")

# Main program logic follows:
if __name__ == '__main__':
    thread = GetDataBackground()
    thread.daemon = True
    thread.start()

    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
    # Intialize the library (must be called once before other functions).
    strip.begin()

    spin_speed = 0.0
    spin = 0.0

    t = .05

    while True:

        scaled = rx_delta / 10.0
        if spin_speed < scaled : spin_speed = spin_speed + (scaled - spin_speed) * .30 * t
        if spin_speed > scaled : spin_speed = spin_speed + (scaled - spin_speed) * .20 * t
        if spin_speed < 0 : spin_speed = 0

        #print("scaled:        " + str(scaled))
        #print("spin_speed:    " + str(spin_speed))

        spin = spin + spin_speed

        for i in range(strip.numPixels()) :
            dist = math.sin((i + spin) / 24.0 * 3.1416 * 2.0)
            if dist < 0 : dist = 0
            dist = dist * dist * dist
            strip.setPixelColorRGB(i, int(0xff * dist), 0x00, 0x00);

            #if i == int(spin) % LED_COUNT :
            #    strip.setPixelColor(i, wheel(i & 255))
            #else :
            #    strip.setPixelColor(i, Color(0, 0, 0))

        strip.show()

        time.sleep(t)
