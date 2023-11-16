from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count
from Worker import Worker, DONE
from numpy import array_split, ndarray, concatenate
from timeit import timeit

LENGTH = 9
MIN = 0
MAX = 5
N_WORKERS = 4
HORIZONTAL_PARTITIONS = 3
VERTICAL_PARTITIONS = 3
SHOTS = 1
SIG_FIGS = 5

# TODO Fix simulations()
# TODO Add Semaphore and/or Lock
# TODO Add input validation
# TODO try-except statements

class Manager(ProcessPoolExecutor):
    def __init__(self, matrix_1: ndarray, matrix_2: ndarray, processes: int = N_WORKERS):
        super().__init__()
        self._results = { }
        self._m1_partitions = Manager.partition(self, matrix_1)
        self._m2_partitions = Manager.partition(self, matrix_2)
        
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

    def partition(self, matrix: ndarray) -> list:
        """
        Partition matrix into submatrices

        Args:
            matrix (ndarray): Matrix to be partitioned

        Returns:
            list: Partitioned matrix
        """
        # Check if matrix is 1D (i.e. vector)
        if matrix.ndim == 1: return array_split(matrix, VERTICAL_PARTITIONS, axis = 0)

        # Split matrix horizontally
        sub_matrices = array_split(matrix, HORIZONTAL_PARTITIONS, axis = 0)
        
        # Split submatrices vertically then return
        return [m for sub_matrix in sub_matrices for m in  array_split(sub_matrix, VERTICAL_PARTITIONS, axis = 1)]

    def allocate_work(self) -> None:
        """
        Allocated work for each process
        """
        # Putting an item in the workers queue will cause it to run
        for i in range(len(self._m1_partitions)):
            self._workers[i % self._process_count]._in_queue.put((self._m1_partitions[i], self._m2_partitions[i % VERTICAL_PARTITIONS], i))

        # Finalize all workers
        for worker in self._workers:
            worker._in_queue.put(DONE)

        # Join all workers
        for worker in self._workers:
            worker.join()

    def combine_results(self) -> ndarray:
        """
        Combines all separate submatrices into a single matrix

        Returns:
            ndarray: Combined result of given matrices
        """
        combined_results, end = [], 0
        results = [value for _, value in sorted(self._results.items())]

        # Sum all values in the same row, then add to combined_results
        for i in range(0, len(results), VERTICAL_PARTITIONS):
            end += VERTICAL_PARTITIONS
            combined_results.append(sum(results[i:end]))

        # Combine all results into a single matrix
        return concatenate(combined_results)

    def get_results(self) -> ndarray:
        """
        Get final result

        Returns:
            ndarray: Result of multiplying Matrix #1 and Matrix #2
        """
        Manager.allocate_work(self)
        
        for i in range(len(self._m1_partitions)):
            result, index = self._workers[i % self._process_count]._out_queue.get()
            self._results[index] = result

        return Manager.combine_results(self)

    def print_submatrices(self, submatrices: list) -> None:
        """
        Prints each of the given submatrices

        Args:
            submatrices (list): Submatrices to be printed
        """
        # Print each submatrix separated by a newline
        for submatrix in submatrices[:-1]:
            print("%s\n" % submatrix)

        # Print last submatrix without a newline
        print("%s" % submatrices[-1])

    def debug_print(self) -> None:
        """
        Print submatrices (i.e. partitions) for debugging
        """
        print("\nSTART:", len(self._m1_partitions), "SUBMATRICES FOR MATRIX #1")
        Manager.print_submatrices(self, self._m1_partitions)
        print("END:", len(self._m1_partitions), "SUBMATRICES FOR MATRIX #1\n")

        print("START:", len(self._m2_partitions), "SUBMATRICES FOR MATRIX #2")
        Manager.print_submatrices(self, self._m2_partitions)
        print("END:", len(self._m2_partitions), "SUBMATRICES FOR MATRIX #2\n")

    def timing(self, func: str, setup: str, sims: int = SHOTS) -> float:
        """
        Define general timing function for simulations

        Args:
            func (str): Function to simulate
            setup (str): Necessary imports and variables
            sims (int, optional): Number of simulations; defaults to SHOTS

        Returns:
            float: Average calculation time (in milliseconds) for func after simulations
        """
        return timeit(func, f"from __main__ import {setup}", number = sims) * 1000

    # TODO Fix this method
    def simulations(self, matrix_1: ndarray, matrix_2: ndarray) -> None:
        """
        Runs simulations for each
        (1) Individual step in get_results()
        (2) Calculation type (i.e. get_results(), matmul(), einsum())
        Prints their results, and determines the quickest calculation

        Args:
            matrix_1 (ndarray): Matrix #1 with length and width = LENGTH
            matrix_2 (ndarray): Matrix #2 with length = LENGTH
        """
        # Import and input strings for timing
        input = f"{matrix_1}, {matrix_2}"
        partition_1 = f"partition({matrix_1})"
        partition_2 = f"partition({matrix_2})"
        process_results = f"allocate_work()"
        imports = "numpy, MIN, MAX, LENGTH"
        
        # Simulate calculations for each individual step in calculate_result()
        print("PARTITION MATRIX #1 TIME =", round(Manager.timing(self, f"{partition_1}", f"{imports}, partition"), SIG_FIGS), "MS")
        print("PARTITION MATRIX #2 TIME =", round(Manager.timing(self, f"{partition_2}", f"{imports}, partition"), SIG_FIGS), "MS")
        print("ALLOCATE WORK TIME =", round(Manager.timing(self, f"{process_results}", f"{imports}, processing, partition"), SIG_FIGS), "MS")
        print("COMBINE RESULTS TIME =", round(Manager.timing(self, f"combine_results({process_results})", f"{imports}, combine_results, processing, partition"), SIG_FIGS), "MS")

        # Simulate calculations for each method of matrix multiplication
        c_time = Manager.timing(self, f"calculate_result({input})", f"{imports}, get_results")
        m_time = Manager.timing(self, f"np.matmul({input})", imports)
        e_time = Manager.timing(self, f"np.einsum('ij,j->i', {input})", imports)
        
        # Print time calculations
        print("get_results() TIME =", round(c_time, SIG_FIGS), "MS")
        print("matmul() TIME =", round(m_time, SIG_FIGS), "MS")
        print("einsum() TIME =", round(e_time, SIG_FIGS), "MS")
        
        # Determine quickest calculation
        minimum = min(e_time, c_time, m_time)
        if minimum == e_time: print("einsum() IS %f MS FASTER THAN get_results()\n" % round(abs(c_time - e_time), SIG_FIGS))
        elif minimum == m_time: print("matmul() IS %f MS FASTER THAN get_results()\n" % round(abs(c_time - m_time), SIG_FIGS))
        else: print("get_results() IS THE FASTEST\n")

# if __name__ == "__main__":
#     # Partition Matrix #1 into submatrices
#     m1_results = partition(np.random.randint(MIN, MAX, size = (LENGTH, LENGTH)))
    
#     # Partition Matrix #2 into submatrices
#     m2_results = partition(np.random.randint(MIN, MAX, size = LENGTH))

#     manager = Manager(m1_results, m2_results)
    
#     print(manager.get_results())