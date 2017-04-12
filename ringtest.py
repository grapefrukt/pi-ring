from neopixel import *
from pysnmp.hlapi import *
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
BW_FREQUENCY   = 3       # Delay in seconds between polls of bandwidth data

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


upstream = [0]*(BW_SAMPLES)
downstream = [0]*(BW_SAMPLES)

display = 0.0

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
    cmd = getCmd(SnmpEngine(),
         CommunityData('public', mpModel=1),
         UdpTransportTarget(('192.168.2.1', 161)),
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
        downstream.append(int(varBinds[0][1]))
        upstream.append(int(varBinds[1][1]))
        
        if len(downstream) > BW_SAMPLES : downstream.pop(0)
        if len(upstream) > BW_SAMPLES : upstream.pop(0)

# Main program logic follows:
if __name__ == '__main__':
    thread = GetDataBackground()
    thread.daemon = True
    thread.start()

    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
    # Intialize the library (must be called once before other functions).
    strip.begin()

    while True:
        delta = downstream[len(downstream) - 1] - downstream[len(downstream) - 2]

        display += (display - delta) * .1

        print(delta)
        print(display)
        
        for i in range(strip.numPixels()) :
            
            #if display / 8000 > i :
            strip.setPixelColor(i, wheel(i & 255))
          #  else :
          #      strip.setPixelColor(i, Color(0, 0, 0))

        strip.show()
        
        time.sleep(1)
