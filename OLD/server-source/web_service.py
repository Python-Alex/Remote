import sys
import time
import json
import flask
import binascii
import threading

import requests

flask_server : flask.Flask = flask.Flask(__name__)

__version__ = (0, 0, 1)
__updated__ = "2021-11-05 08:53:20"

routes = ['/wbla/authenticate', '/wbla/decomission', '/dvi/cpu-information', '/dvi/system-information', '/dvi/fstructure-information', '/dve/report-package-status']
required_packages = ['py-cpuinfo', 'psutil', 'requests']

hex_routes = {route: '/' + str(binascii.b2a_hex(route.encode()).decode()) for route in routes}

class FlaskServerWrapper(flask.Flask):
    """
    route json content should always contain a 'content' key inside the json data.

    """

    __lock__ : bool = False # controls all sub-class threads
    instance : object = None

    class DeviceAuthorization(object):
        def __init__(self):
            FlaskServerWrapper.instance.add_url_rule(
                hex_routes['/wbla/authenticate'], 
                endpoint='authenticate', 
                view_func=self.authenticate_request, 
                provide_automatic_options=None, methods=['POST']
            )
            FlaskServerWrapper.instance.add_url_rule(
                hex_routes['/wbla/decomission'], 
                endpoint='decomission', 
                view_func=self.decomission_request, 
                provide_automatic_options=None, methods=['POST']
            )

            self.devices = {} # 'address': {}

        def authenticate_request(self): # device authorize
            request_sender = flask.request.remote_addr

            if(request_sender in [v for v in self.devices.keys()]):
                return json.dumps({'message': 'already authenticated'}), 405

            authorization_header = flask.request.headers.get('Authorization') # client name 

            self.devices.update({
                request_sender: {
                    'name': authorization_header, 
                    'frame': time.time(), 
                    'query': {
                        'fstructure-information': {},
                        'cpu-information': (),
                        'system-information': ()
                    },
                    'scan-uploading': False,
                    'scan-completed': False}
                })

            return json.dumps({'message': 'OK'}), 200

        def decomission_request(self): # client logout
            request_sender = flask.request.remote_addr

            if(request_sender not in [v for v in self.devices.keys()]):
                return json.dumps({'message': 'not authenticated'}), 405
            
            del self.devices[request_sender]

            return json.dumps({'message': 'OK'}), 200

    class DeviceInteract(object):
        def __init__(self):    
            FlaskServerWrapper.instance.add_url_rule(
                hex_routes['/dvi/fstructure-information'],
                endpoint='fstructure_information',
                view_func=self.process_fstructure_update,
                provide_automatic_options=None, methods=['POST']
            )
            FlaskServerWrapper.instance.add_url_rule(
                hex_routes['/dvi/cpu-information'],
                endpoint='cpu_information',
                view_func=self.process_cpuinfo_update,
                provide_automatic_options=None, methods=['POST']
            )
            FlaskServerWrapper.instance.add_url_rule(
                hex_routes['/dvi/system-information'],
                endpoint='system_information',
                view_func=self.process_system_update,
                provide_automatic_options=None, methods=['POST']
            )

        def process_fstructure_update(self):
            request_frame = flask.request.get_json()
            request_sender = flask.request.remote_addr

            device = FlaskServerWrapper.instance.device_authorization.devices.get(request_sender)
            if(not device):
                return json.dumps({'message': 'not authenticated'}), 403

            if(not request_frame or not request_frame.get('content')):
                return json.dumps({'message': 'empty content'}), 405

            if(request_frame['status'] == 1):
                device['scan-uploading'] = True

                for disk in request_frame['content']:
                    device['query']['fstructure-information'][disk] = [[], []]

                return json.dumps({'message': 'OK'}), 200

            if(request_frame['status'] == 0):
                device['scan-completed'] = True; device['scan-uploading'] = False
                return json.dumps({'message': 'OK'}), 200

            if(request_frame['status'] == 2):
            #print(device['query']['fstructure-information'].keys(), request_frame.keys())
                device['query']['fstructure-information'][request_frame['disk']][0].extend(request_frame['content']['directories'])
                device['query']['fstructure-information'][request_frame['disk']][1].extend(request_frame['content']['files'])
            
            return json.dumps({'message': 'OK'}), 200

        def process_cpuinfo_update(self):
            request_frame = flask.request.get_json()
            request_sender = flask.request.remote_addr

            device = FlaskServerWrapper.instance.device_authorization.devices.get(request_sender)
            if(not device):
                return json.dumps({"message": "not authenticated"}), 403

            if(not request_frame or not request_frame.get('content')):
                return json.dumps({"message": "empty content"}), 405

            device['query']['cpu-information'] = request_frame['content']
            
            return json.dumps({"message": "OK"}), 200

        def process_system_update(self):
            request_frame = flask.request.get_json()
            request_sender = flask.request.remote_addr

            device = FlaskServerWrapper.instance.device_authorization.devices.get(request_sender)
            if(not device):
                return json.dumps({'message': 'not authenticated'}), 403

            if(not request_frame or not request_frame.get('content')):
                return json.dumps({'message': 'empty content'}), 405

            device['query']['system-information'] = request_frame['content']
            return json.dumps({"message": "OK"}), 200

    class DeviceExecution(object):
        def __init__(self) -> None:
            FlaskServerWrapper.instance.add_url_rule(
                hex_routes['/dve/report-package-status'],
                endpoint='report_package_status',
                view_func=self.report_package_status,
                provide_automatic_options=None, methods=['POST']
            )

        def report_package_status(self):
            return

    def __init__(self, app_name: str = __name__):
        flask.Flask.__init__(self, import_name=app_name)
        self.__class__.instance = self

        self.device_authorization = FlaskServerWrapper.DeviceAuthorization()
        self.device_interaction   = FlaskServerWrapper.DeviceInteract()

x = FlaskServerWrapper()

@x.route('/mapping', methods=['GET'])
def return_mapping():
    return json.dumps(hex_routes)
    
x.run('127.0.0.1', 9909)