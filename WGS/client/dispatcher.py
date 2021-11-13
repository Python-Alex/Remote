import threading
import requests
import time
import iapi

LSLEEP = 0.1
LSLEEP /= 10000000000000

class Dispatcher(threading.Thread):

    instance : object = None
    __lock__ : bool = False

    def __init__(self):
        threading.Thread.__init__(self, name='Dispatcher')
        self.__class__.instance = self
        self.events = []

    def new_event(self, client: object, flag: int, content: dict):
        self.events.append((client, flag, content))

    def run(self):
        while(not self.__class__.__lock__):
            for event in self.events.copy():
                try:
                    requests.post(f'{iapi.server_ws_addr}register_action', json={'flag': event[1], 'content': event[2]})
                except requests.exceptions.ConnectionError as stream_error:
                    iapi.server_ack = False

                except Exception as global_error:
                    print(type(global_error), global_error)

                self.events.remove(event)

            time.sleep(LSLEEP)

Dispatcher().start()