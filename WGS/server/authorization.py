import os
import time
import json
import base64
import hashlib
import threading
import classtypes

class AlreadyAuthorized(Exception):

    def __init__(self, *args):
        Exception.__init__(self, *args)

class ClientInformationCache(threading.Thread):

    __lock__ : bool = False

    def __init__(self):
        threading.Thread.__init__(self, name='ClientInformationCache')
        self.client_cache = {}
        self.reloading_client_frame = False

    def run(self):
        while(not self.__lock__):
            self.reloading_client_frame = True

            for account in os.listdir(os.getcwd() + '\\server\\disk\\accounts'):
                client_info = {}
                
                for (json_key, json_value) in json.loads(open(os.getcwd() + '\\server\\disk\\accounts\\' + account + "\\ClientInformation.json", "r").read()).items():
                    client_info.update({json_key: json_value})

                # check if the connection is already existing?
                 

            self.reloading_client_frame = False

            time.sleep(2.5)

username = 'Void'
password = 'AdminVoid'

serialized = base64.b64encode(str(username + password).encode())
print(serialized)
hashed = hashlib.md5(serialized).hexdigest()
print(hashed)

ClientInformationCache().start()