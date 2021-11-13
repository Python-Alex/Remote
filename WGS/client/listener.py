import sys
import time
import json
import enum
import flask
import iapi
import requests
import threading

server_ws_addr = 'http://127.0.0.1:9999/'
client_ws = flask.Flask(__name__)

iapi.server_ws_addr = server_ws_addr

userid = hash(client_ws)

threading.Thread(target=client_ws.run, args=('127.0.0.1', 9090)).start()

Client = iapi.Client()

# tell server we're connecting
@client_ws.route('/receive_action', methods=['POST'])
def receive_action():
    request = flask.request

    packet_content = request.get_json()
    packet_flag = int(packet_content.get('flag'))

    if(not packet_flag or not packet_content):
        return json.dumps({
            'error': 0xE1,
            'message': 'bad integrity'
        })

    rcallback = iapi.reverse_aflag_map[int(packet_flag)]
    rcallback(flask.request, **packet_content)

    return ''

