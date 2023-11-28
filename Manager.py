from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count
from Worker import Worker, DONE
from numpy import array_split, ndarray, concatenate
from Shared import LENGTH, MATRIX_2_WIDTH, HORIZONTAL_PARTITIONS, VERTICAL_PARTITIONS, generate_matrix, combine_results, print_outcome

N_WORKERS = 4

# TODO Add input validation
# TODO try-except statements
# TODO Include main as 1 of the processes (i.e. Workers)

class Manager(ProcessPoolExecutor):
    def __init__(self, matrix_1: ndarray, matrix_2: ndarray, processes: int = N_WORKERS):
        super().__init__()
        # Dict containing results from each process (matrix multi)
        self._results = { }

        # Matrix #1 partitions
        self._m1_partitions = Manager.partition_m1(self, matrix_1)

        # Matrix #2 partitions
        self._m2_partitions = Manager.partition_m2(self, matrix_2)

        # Make sure number of processes is valid
        if processes < 1 or processes > cpu_count():
            raise ValueError(f"Number of processes must be greater than 1 and less than or equal to the number of CPUs in the system, i.e. {cpu_count()}")
        self._process_count = processes

        self._workers = Manager.init_workers(self)

    def init_workers(self) -> list[Worker]:
        """
        Instantiate and start processes

        Returns:
            list[Worker]: List of processes
        """
        workers = [Worker() for _ in range(self._process_count)]
        
        for worker in workers:
            worker.start()

        return workers

    def partition_m1(self, matrix: ndarray) -> list:
        """
        Partition Matrix #1 into submatrices

        Args:
            matrix (ndarray): Matrix #1 to be partitioned

        Returns:
            list: Partitioned Matrix #1
        """
        # Check if matrix is 1D (i.e. vector)
        if matrix.ndim == 1: return Manager.partition_m2(self, matrix)
        
        # Split matrix horizontally
        sub_matrices = array_split(matrix, HORIZONTAL_PARTITIONS, axis = 0)
        
        # Split submatrices vertically, then return
        return [m for sub_matrix in sub_matrices for m in  array_split(sub_matrix, VERTICAL_PARTITIONS, axis = 1)]

    def partition_m2(self, matrix: ndarray) -> list:
        """
        Partition Matrix #2 into submatrices

        Args:
            matrix (ndarray): Matrix #2 to be partitioned

        Returns:
            list: Partitioned Matrix #2
        """
        return array_split(matrix, VERTICAL_PARTITIONS, axis = 0)

    def allocate_work(self) -> None:
        """
        Allocated work for each process
        """
        # Putting an item in the workers queue will cause it to run
        for i in range(len(self._m1_partitions)):
            self._workers[i % self._process_count].in_queue.put((self._m1_partitions[i], self._m2_partitions[i % VERTICAL_PARTITIONS], i))

        # Finalize all workers
        for worker in self._workers:
            worker.in_queue.put(DONE)

        # Join all workers
        for worker in self._workers:
            worker.join()

    def get_result(self) -> ndarray:
        """
        Get final result

        Returns:
            ndarray: Result of multiplying Matrix #1 and Matrix #2
        """
        Manager.allocate_work(self)
        
        for i in range(len(self._m1_partitions)):
            result, index = self._workers[i % self._process_count].out_queue.get()
            self._results[index] = result

        return combine_results(self._results)

if __name__ == "__main__":
    # Matrix #1
    matrix_1 = generate_matrix(LENGTH, LENGTH)
    
    # Matrix #2
    matrix_2 = generate_matrix(LENGTH, MATRIX_2_WIDTH)

    # Create Manager to multiply the matrices with multiprocessing
    manager = Manager(matrix_1, matrix_2)

    # Print outcome
    print_outcome(manager.get_result(), matrix_1 @ matrix_2)