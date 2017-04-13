import netinfo

router_ip = ''

for route in netinfo.get_routes() :
#    print route['dest'] #+" -> "+route['gateway']
    if route['dest'] == '0.0.0.0' :
	router_ip = route['gateway']

print 'router is at ' + router_ip
