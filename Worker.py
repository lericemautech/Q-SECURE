from multiprocessing import Process, Queue

# States
INIT = "INIT"
RUN = "RUN"
CLOSE = "CLOSE"
TERMINATE = "TERMINATE"
STOP = "STOP"

# Number of processes
N_POOLS = 4

class Worker(Process):
    def __init__(self, target, args = (), kwargs = {}, name = str(), daemon = True):
        """
        Initialize Worker

        Args:
            target: Function to execute
            args: Arguments to pass to function; defaults to ()
            kwargs: Keyword arguments to pass to function; defaults to {}
            name: Process name; defaults to empty string
            daemon: Whether process is daemon or not; defaults to True
        """
        #Process.__init__(self, target = target, args = args, kwargs = kwargs, name = name, daemon = daemon)
        super(Worker, self).__init__(target = target, args = args, kwargs = kwargs, name = name, daemon = daemon)
        self._target = target
        self._args = tuple(args)
        self._kwargs = dict(kwargs)
        self._name = str(name)
        self._daemon = daemon
        self._queue = Queue()
        self._result = None
        self._state = INIT

    def run(self):
        """
        Run process
        """
        self._state = RUN
        while not self._queue.empty():
            self._target(*self._args)
            #self._target(*self._queue.get())
        self._state = CLOSE

        # for arg in iter(self._queue.get, STOP):
        #     self._target(*arg)
            
        # self._state = RUN
        # self._result = self._target(*self._args, **self._kwargs)
        # self._state = CLOSE

    @property
    def result(self):
        """
        Get result of process

        Returns:
            Any: Process result
        """
        return self._result

    @property
    def name(self) -> str:
        """
        String used for process identification

        Returns:
            str: Process name
        """
        return self._name

    @name.setter
    def name(self, name: str):
        """
        Set process name

        Args:
            name (str): Process name
        """
        self._name = name

    def is_alive(self) -> bool:
        """
        Checks if process is alive or not

        Returns:
            bool: True if process is alive, else False
        """
        return super().is_alive()