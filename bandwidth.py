from pysnmp.hlapi import *
import time

while True :
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
        for varBind in varBinds:
            print(' = '.join([x.prettyPrint() for x in varBind]))
    
    time.sleep(1)
