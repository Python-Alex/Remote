import sys
import time
import threading
import functools

sys.stdout.write(f'[*] Loading Reference {__name__}\n')

__updated__ = '2021-10-31 16:55:56'

LSLEEP = 0.1
LSLEEP /= 10000000000000

class TimedQueue(threading.Thread):

    instances : list = []
    cwm_instances : list = []
    awm_instances : list = []

    __lock__ : bool = False
    reference : object = None

    def __init__(self) -> None:
        threading.Thread.__init__(self, name='TimedQueue')

        sys.stdout.write(f'[*] [THREAD] {self.__class__.__name__} Initialized ({hex(id(self))})\n')

        if(self.__class__.reference):
            raise AttributeError('already defined!')

        self.__class__.reference = self

        self.start()

    def run(self):
        sys.stdout.write(f'[*] [THREAD] {self.__class__.__name__} Started ({hex(id(self))})\n')
        
        instances = iter(self.__class__.instances)
        cwm_instances = iter(self.__class__.cwm_instances)
        awm_instances = iter(self.__class__.awm_instances)

        while(not self.__class__.__lock__):
            try:
                instance = next(instances)
                if(time.time() - instance[4] >= instance[0]):
                    instance[1](*instance[2], **instance[3])

                    instance[4] = time.time()
            except StopIteration:
                instances = iter(self.__class__.instances)

            try:
                cwm_instance = next(cwm_instances)
                if(cwm_instance[0]() == True):
                    self.__class__.cwm_instances.remove(cwm_instance)
                    cwm_instance[1](*cwm_instance[2], **cwm_instance[3])
            except StopIteration:
                cwm_instances = iter(self.__class__.cwm_instances)

            try:
                awm_instance = next(awm_instances)
                if(awm_instance[0]() == awm_instance[1]):
                    self.__class__.cwm_instances.remove(cwm_instance)
                    cwm_instance[2](*cwm_instance[3], **cwm_instance[4])
            except StopIteration:
                cwm_instances = iter(self.__class__.cwm_instances)


            time.sleep(LSLEEP)

    # don't call this. ever, only use as a decorator
    def throttle_function(self, interval: float, execute_first: bool = False):
        """ calls function everytime the interval is passed in unix time
        
        execute_first : execute the function as soon as its defined
        """
        def function_wrapper(function: callable):
            @functools.wraps(function)
            def _fwr(*args, **kwargs):
                sys.stdout.write(f'[*] [THREAD] {self.__class__.__name__} NEW THROTTLE FUNCTION ({hex(id(function))})\n')

                if(execute_first):
                    function(*args, *kwargs)
                self.__class__.instances.append([interval, function, args, kwargs, time.time()])
                
            return _fwr

        return function_wrapper

    def execute_when_true(self, wt_function: callable):
        """ calls function everytime the wt_function is True, deletes after call"""

        def function_wrapper(function: callable):
            @functools.wraps(function)
            def _fwr(*args, **kwargs):
                sys.stdout.write(f'[*] [THREAD] {self.__class__.__name__} (EXEC_W_TRUE) NEW LOGICAL EXPRESSION ({hex(id(function))})\n')
                self.__class__.cwm_instances.append((wt_function, function, args, kwargs))

            return _fwr

        return function_wrapper

    def execute_when_equals(self, we_function: callable, equal_var: any):
        """ calls function everytime the we_function matches equal_var, deletes after call"""
        def function_wrapper(function: callable):
            @functools.wraps(function)
            def _fwr(*args, **kwargs):
                sys.stdout.write(f'[*] [THREAD] {self.__class__.__name__} (EXEC_W_EQUALS) NEW LOGICAL EXPRESSION ({hex(id(function))})\n')
                self.__class__.awm_instances.append((we_function, equal_var, function, args, kwargs))

            return _fwr

        return function_wrapper

    def remove_entry(self, function: callable):
        for instance in self.__class__.instances.copy():
            if(instance[1] == function):
                sys.stdout.write(f'[*] [THREAD] {self.__class__.__name__} REMOVED ENTRY ({hex(id(function))})\n')
                self.__class__.instances.remove(instance)
                break

try:
    GlobalTimeQueue = TimedQueue()
except AttributeError:
    GlobalTimeQueue = TimedQueue.reference