from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Queue, JoinableQueue, Semaphore, cpu_count
from Worker import Worker
from time import sleep

N_WORKERS = 4
N_SEMAPHORES = 2
VERTICAL_PARTITIONS = 2
TIME = 1

# States
INIT = "INIT"
RUN = "RUN"
IDLE = "IDLE"
DONE = "DONE"

class Manager(ProcessPoolExecutor):
    def __init__(self, m1_results: list, m2_results: list, processes: int = N_WORKERS, semaphore = Semaphore(N_SEMAPHORES)):
        super().__init__()
        self._workers = Manager.init_workers(self)
        self._tasks = Manager.init_queue(self, m1_results, m2_results)
        self._results: Queue = Queue()
        self._semaphore = semaphore
        
        if processes < 1 or processes > cpu_count():
            raise ValueError(f"Number of processes must be greater than 1 and less than or equal to the number of CPUs in the system, i.e. {cpu_count()}")
        self._process_count = processes

    def init_workers(self) -> list[Worker]:
        """
        Instantiate and start processes

        Returns:
            list[Worker]: List of processes
        """
        workers = [ Worker() for _ in range(self._process_count) ]
        
        for worker in workers:
            worker.start()

        return workers

    def init_queue(self, m1_results: list, m2_results: list) -> JoinableQueue:
        """
        Initialize input Queue for processes

        Args:
            m1_results (list): Matrix #1 partitioned into submatrices
            m2_results (list): Matrix #2 partitioned into submatrices

        Returns:
            JoinableQueue: _description_
        """
        queue = JoinableQueue()
        
        for i in range(len(m1_results)):
            queue.put((m1_results[i], m2_results[i % VERTICAL_PARTITIONS]))

        return queue

    def allocate_work(self) -> None:
        """
        Allocate work to processes
        """
        while not self._tasks.empty():
            self._semaphore.acquire()
            sleep(TIME)
            self._semaphore.release()

        # for worker in self.workers:
        #     worker.in_queue.put(self.in_queue.get())

if __name__ == "__main__":
    m1_results = [ ]
    m2_results = [ ]

    manager = Manager(m1_results, m2_results)
        
    # Putting an item in the workers queue will cause it to run
    manager._workers[0]._in_queue.put("Hello")
    manager._workers[1]._in_queue.put("world")
    manager._workers[2]._in_queue.put("I'm")
    manager._workers[3]._in_queue.put("so")
    manager._workers[1]._in_queue.put("swag")
    manager._workers[2]._in_queue.put("!!!")

    # Finalize all workers
    for worker in manager._workers:
        worker._in_queue.put(DONE)

    for worker in manager._workers:
        worker.join()

    for worker in manager._workers:
        print(worker._out_queue.get())