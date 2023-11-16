from multiprocessing import Process, Queue
from numpy import ndarray

# State
DONE = "DONE"

class Worker(Process):
    def __init__(self, daemon = True):
        super().__init__(daemon = daemon)
        self._in_queue = Queue()
        self._out_queue = Queue()

    def matrix_vector_mult(self, matrix_1: ndarray, matrix_2: ndarray, index: int) -> tuple[ndarray, int]:
        """
        Multiply 2 matrices

        Args:
            matrix_1 (ndarray): Matrix #1
            matrix_2 (ndarray): Matrix #2
            index (_type_): Matrix position

        Returns:
            tuple[ndarray, int]: Multiple of matrix_1 and matrix_2, index
        """
        return matrix_1 @ matrix_2, index

    def run(self) -> None:
        # Blocks until something available, exits when receiving "DONE"
        for arg in iter(self._in_queue.get, DONE):
            matrix_1, matrix_2, index = arg
            result = Worker.matrix_vector_mult(self, matrix_1, matrix_2, index)
            self._out_queue.put(result)
            #print(f"Worker {self.pid} result = {result}, index = {index}", flush = True)