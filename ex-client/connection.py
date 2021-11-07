import sys
import time
import json
import flask
import socket
import requests

base_url = 'http://127.0.0.1:9909'

routes = json.loads(requests.get(base_url + '/mapping').text)
time.sleep(0.2)

r = requests.post(base_url + routes['/wbla/authenticate'], headers={'Authorization': 'Device-%d' % (hash(sys))})
time.sleep(0.1)
if(r.status_code == 405):
    requests.post(base_url + routes['/wbla/decomission'])
    time.sleep(0.1)
    requests.post(base_url + routes['/wbla/authenticate'], headers={'Authorization': 'Device-%d' % (hash(sys))})