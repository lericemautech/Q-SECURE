from multiprocessing import Process, Queue
from numpy import ndarray

# State
DONE = "DONE"

class Worker(Process):
    def __init__(self, daemon = True):
        super().__init__(daemon = daemon)

        # Queue of matrices to be multiplied
        self._in_queue = Queue()

        # Multiplication result
        self._out_queue = Queue()

    def matrix_vector_mult(self, matrix_1: ndarray, matrix_2: ndarray, index: int) -> tuple[ndarray, int]:
        """
        Multiply 2 matrices

        Args:
            matrix_1 (ndarray): Matrix #1
            matrix_2 (ndarray): Matrix #2
            index (int): Matrix position

        Returns:
            tuple[ndarray, int]: Multiple of matrix_1 and matrix_2, index
        """
        return matrix_1 @ matrix_2, index

    def run(self) -> None:
        """
        Run process
        """
        # Blocks until something available, exits when receiving "DONE"
        for arg in iter(self._in_queue.get, DONE):
            # Unpack arguments (i.e. matrices and index)
            matrix_1, matrix_2, index = arg

            # Multiply matrices
            result = Worker.matrix_vector_mult(self, matrix_1, matrix_2, index)

            # Add result to output queue
            self._out_queue.put(result)
            
            print(f"Worker {self.pid} result = {result[0]}, index = {index}", flush = True)