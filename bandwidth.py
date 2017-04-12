from pysnmp.hlapi import *
import time
import threading


BW_SAMPLES      = 5      # Number of bandwidth samples to keep
BW_FREQUENCY    = 3       # Delay in seconds between polls of bandwidth data

upstream = [0]*(BW_SAMPLES)
downstream = [0]*(BW_SAMPLES)

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

    while True :
        delta = downstream[len(downstream) - 1] - downstream[len(downstream) - 2]
        print(delta)

        time.sleep(3)