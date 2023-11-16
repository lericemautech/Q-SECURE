from multiprocessing import Process, JoinableQueue

# States
INIT = "INIT"
RUN = "RUN"
IDLE = "IDLE"
DONE = "DONE"

class Worker(Process):
    def __init__(self, daemon = True):
        super().__init__(daemon = daemon)
        self._state: str = INIT
        self._in_queue = JoinableQueue()
        self._out_queue = JoinableQueue()

    def run(self):
            print(f"Worker {self.pid} starting", flush = True)
            self.state = RUN
            # Blocks until something available, exits when receiving "DONE"
            for arg in iter(self._in_queue.get, DONE):
                # Perform work (with arg?)
                print(arg)
                #self._in_queue.task_done()
            self.state = DONE
            print("fWorker {self.pid} ending", flush = True)
            self.state = IDLE

    @property
    def state(self) -> str:
        """
        Worker's state

        Returns:
            str: Worker's current state
        """
        return self._state

    @state.setter
    def state(self, state: str):
        if state not in [INIT, RUN, DONE, IDLE]:
            raise ValueError(f"Invalid state: {state}")
        self._state = state