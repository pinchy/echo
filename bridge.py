# Alexa Razberry Bridge
# Sebastien Eckersley-Maslin (@pinchy)
# Forked from toddmedema/echo
# 
# This file scanns the Razberry devices API and creates a list
# of controllable devices defined with the 'alexa' tag in the
# Razberry UI
# Each device becomes discoverable as a WeMo device by Alexa
# and the simple name in the Razberry UI is used to control 
# the device

import fauxmo
import logging
import time
import requests
import json
import array

from debounce_handler import debounce_handler

#global
devices = []
s = requests.Session()
server = 'http://localhost:8083'

logging.basicConfig(level=logging.DEBUG)

class device_handler(debounce_handler):
    """Publishes the on/off state requested,
       and the IP address of the Echo making the request.
    """

    login_url = server + '/ZAutomation/api/v1/login'
    devices_url= server +'/ZAutomation/api/v1/devices'

    username = 'USERNAME'
    password = 'PASSWORD'

    login_header = {'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json'}
    form_login = '{"form": true, "login": "'+username+'", "password": "'+password+'", "keepme": false, "default_ui": 1}'

    s.post(login_url,headers=login_header, data=form_login)

    r = s.get(devices_url)
    html = r.text
    device_json = r.json()

    for device in device_json['data']['devices'] :
        if 'alexa' in device['tags']:
            devices.append(device)

    devices.sort()


    def act(self, client_address, state, name):
        for device in devices :
            if device['metrics']['title'] == name :
                if state == True:
                    r = s.get(server + '/ZAutomation/api/v1/devices/' + device['id'] + '/command/on')
                else:
                    r = s.get(server + '/ZAutomation/api/v1/devices/' + device['id'] + '/command/off')

                print r.status_code

        print "State", state, "on ", name, "from client @", client_address
        return True


if __name__ == "__main__":
    # Startup the fauxmo server
    fauxmo.DEBUG = True
    p = fauxmo.poller()
    u = fauxmo.upnp_broadcast_responder()
    u.init_socket()
    p.add(u)

    # Register the device callback as a fauxmo handler
    d = device_handler()
    port = 52000

    for device in devices:
    #for trig, port in d.TRIGGERS.items():
        fauxmo.fauxmo(device['metrics']['title'], u, p, None, port, d)
        port = port + 1

    # Loop and poll for incoming Echo requests
    logging.debug("Entering fauxmo polling loop")
    while True:
        try:
            # Allow time for a ctrl-c to stop the process
            p.poll(100)
            time.sleep(0.1)
        except Exception, e:
            logging.critical("Critical exception: " + str(e))
            break
