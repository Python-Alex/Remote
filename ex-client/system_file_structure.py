import os
import sys
import time
import string
import threading

available_disks = []

for disk_name in string.ascii_uppercase:
    if(os.path.isdir(disk_name + ":\\")):
        available_disks.append(disk_name + ":\\")

path_fmt = "\\" if(os.name == 'nt') else '/'

directory_map = {disk_name: {'directories': [], 'files': []} for disk_name in available_disks}

file_structure_complete = False
running_threads = 0

byte_map = None

def structure_scan(base: str):
    global running_threads
    global directory_map

    running_threads += 1

    for (parent, children, files) in os.walk(base + path_fmt):
        if(parent not in directory_map[base]['directories']):
            directory_map[base]['directories'].append(parent)

        if(children):
            for child in children:
                if(path_fmt not in child.split(path_fmt)[len(child.split(path_fmt)) -1]):
                    child = child + path_fmt

                directory_map[base]['directories'].append(
                    parent + child
                )

        if(files):
            for file in files:
                directory_map[base]['files'].append(parent + path_fmt + file)
    
    running_threads -= 1


def start_structure_threads():
    global byte_map
    global file_structure_complete

    if(threading.current_thread().name == 'MainThread'):
        raise threading.ThreadError('cannot start from the main thread!')

    for start_thread in available_disks:
        threading.Thread(target=structure_scan, args=(start_thread,), name=start_thread).start()
        time.sleep(0.0001)

    while(running_threads != 0):
        #string = ""
        #for disk_map in directory_map.items():
        #    string += f"{disk_map[0]}={len(disk_map[1]['directories'])}/{len(disk_map[1]['files'])}, "
        #    sys.stdout.write(f"\r{running_threads} - {len(threading.enumerate())} - {string}")
        time.sleep(0.000000001)


    file_structure_complete = True
    #byte_map = dill.dumps(directory_map)

def check():
    return file_structure_complete