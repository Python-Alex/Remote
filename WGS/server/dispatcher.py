import sys
import time
import json
import socket
import requests
import threading

from classtypes import ClientInformation

sys.stdout.write(f'[*] Loading Reference {__name__}\n')

LSLEEP = 0.1
LSLEEP /= 10000000000000

class ServerClients(object):
    
    instance : object = None

    def __init__(self) -> None:
        sys.stdout.write(f'[*] [OBJECT] {self.__class__.__name__} Initialized ({hex(id(self))})\n')
        self.clients = []

        self.__class__.instance = self

ServerClients()

class Dispatcher(threading.Thread):

    instance : object = None
    __lock__ : bool = False

    def __init__(self):
        threading.Thread.__init__(self, name='Dispatcher')
        sys.stdout.write(f'[*] [THREAD] {self.__class__.__name__} Initialized ({hex(id(self))})\n')
        self.__class__.instance = self
        self.events = []

    def new_event(self, userid: int, flag: int, content: dict):
        self.events.append((userid, flag, content))

    def run(self):
        sys.stdout.write(f'[*] [THREAD] {self.__class__.__name__} Started ({hex(id(self))})\n')
        while(not self.__class__.__lock__):
            for event in self.events.copy():
                client = ClientInformation.get_cinfo(event[0])
                requests.post(f'http://{client.address}:9090/receive_action', json={'flag': event[1], 'content': event[2]})
                self.events.remove(event)

            time.sleep(LSLEEP)
                

Dispatcher().start()