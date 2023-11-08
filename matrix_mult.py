import numpy as np
from timeit import timeit
from multiprocessing.pool import Pool

LENGTH = 9
HORIZONTAL_PARTITIONS = 3
VERTICAL_PARTITIONS = 3
MIN = 0
MAX = 5
SHOTS = 1
SIG_FIGS = 5
N_POOLS = 4

# TODO Add input validation
# TODO try-except statements

def partition(matrix: np.ndarray) -> list:
    """
    Partition matrix into submatrices

    Args:
        matrix (np.ndarray): Matrix to be partitioned

    Returns:
        list: Partitioned matrix
    """
    # Check if matrix is 1D (i.e. vector)
    if matrix.ndim == 1: return np.array_split(matrix, VERTICAL_PARTITIONS, axis = 0)

    # Split matrix horizontally
    sub_matrices = np.array_split(matrix, HORIZONTAL_PARTITIONS, axis = 0)
    
    # Split submatrices vertically then return
    return [m for sub_matrix in sub_matrices for m in  np.array_split(sub_matrix, VERTICAL_PARTITIONS, axis = 1)]

def matrix_vector_mult(matrix_1: np.ndarray, matrix_2: np.ndarray) -> np.ndarray:
    """
    Multiply 2 matrices

    Args:
        matrix_1 (np.ndarray): Matrix #1
        matrix_2 (np.ndarray): Matrix #2

    Returns:
        np.ndarray: Result of multiplying Matrix #1 and Matrix #2
    """
    return matrix_1 @ matrix_2

def combine_results(results: list) -> np.ndarray:
    """
    Combines all separate submatrices into a single matrix

    Args:
        results (list): List of matrices to combine from Pool

    Returns:
        np.ndarray: Combined result of given matrices
    """
    combined_results, end = [ ], 0

    # Sum all values in the same row, then add to combined_results
    for i in range(0, len(results), VERTICAL_PARTITIONS):
        end += VERTICAL_PARTITIONS
        combined_results.append(sum(results[i:end]))

    # Combine all results into a single matrix
    return np.concatenate(combined_results)

def processing(m1_results: list, m2_results: list) -> list:
    """
    Uses multiprocessing to multiply partitioned matrices

    Args:
        m1_results (list): Matrix #1 partitioned into submatrices
        m2_results (list): Matrix #2 partitioned into submatrices

    Returns:
        list: List of results from each process
    """
    # Create Pool of N_POOLS processes
    pool = Pool(processes = N_POOLS)

    # Multiply each submatrix async and in parallel, get the results, then return
    return [pool.apply_async(matrix_vector_mult, args = (m1_results[i], m2_results[i % VERTICAL_PARTITIONS])).get() for i in range(len(m1_results))]

def print_matrix(matrix: list) -> None:
    """
    Prints given matrix

    Args:
        matrix (list): Matrix to be printed
    """
    i = 1
    for m in matrix:
        # Print each submatrix and its index (starts at 1)
        print("#%i = %s" % (i, m))
        i += 1

def calculate_result(matrix_1: np.ndarray, matrix_2: np.ndarray) -> np.ndarray:
    """
    Matrix multiplication using threads and partitioning

    Args:
        matrix_1 (np.ndarray): Matrix #1 with length and width = LENGTH
        matrix_2 (np.ndarray): Matrix #2 with length = LENGTH

    Returns:
        np.ndarray: Result of multiplying Matrix #1 and Matrix #2
    """
    # Partition Matrix #1 into submatrices
    m1_results = partition(matrix_1)
    
    # Partition Matrix #2 into submatrices
    m2_results = partition(matrix_2)

    # Print submatrices for Matrix #1
    print("Submatrices for Random Matrix #1:")
    print_matrix(m1_results)

    # Print submatrices for Matrix #2
    print("\nSubmatrices for Random Matrix #2:")
    print_matrix(m2_results)

    # Use multiprocessing to multiply the partitioned matrices
    processes = processing(m1_results, m2_results)

    # Combine results into a single vector of size LENGTH
    return combine_results(processes)

def timing(func: str, setup: str, sims: int = SHOTS) -> float:
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
    
def simulations() -> None:
    """
    Runs simulations for each
    (1) Individual step in calculate_result()
    (2) Calculation type (i.e. calculate_result(), matmul(), einsum())
    Prints their results, and determines the quickest calculation
    """
    # Import and input strings for timing
    matrix_1 = "np.random.randint(MIN, MAX, size = (LENGTH, LENGTH))"
    matrix_2 = "np.random.randint(MIN, MAX, size = LENGTH)"
    input = f"{matrix_1}, {matrix_2}"
    partition_1 = f"partition({matrix_1})"
    partition_2 = f"partition({matrix_2})"
    process_results = f"processing({partition_1}, {partition_2})"
    imports = "np, MIN, MAX, LENGTH"
    
    # Simulate calculations for each individual step in calculate_result()
    print("Partition Matrix #1 Time =", round(timing(f"{partition_1}", f"{imports}, partition"), SIG_FIGS), "ms")
    print("Partition Matrix #2 Time =", round(timing(f"{partition_2}", f"{imports}, partition"), SIG_FIGS), "ms")
    print("Processing Time =", round(timing(f"{process_results}", f"{imports}, processing, partition"), SIG_FIGS), "ms")
    print("Combine Results Time =", round(timing(f"combine_results({process_results})", f"{imports}, combine_results, processing, partition"), SIG_FIGS), "ms")

    # Simulate calculations for each method of matrix multiplication
    c_time = timing(f"calculate_result({input})", f"{imports}, calculate_result")
    m_time = timing(f"np.matmul({input})", imports)
    e_time = timing(f"np.einsum('ij,j->i', {input})", imports)
    
    # Print time calculations
    print("\ncalculate_result() Time =", round(c_time, SIG_FIGS), "ms")
    print("Matmul Calculation Time =", round(m_time, SIG_FIGS), "ms")
    print("Einsum Calculation Time =", round(e_time, SIG_FIGS), "ms")
    
    # Determine quickest calculation
    minimum = min(e_time, c_time, m_time)
    if minimum == e_time: print("\nEinsum is %f ms faster than calculate_result()" % round(abs(c_time - e_time), SIG_FIGS))
    elif minimum == m_time: print("\nMatmul is %f ms faster than calculate_result()" % round(abs(c_time - m_time), SIG_FIGS))
    else: print("\ncalculate_result() is somehow the fastest")
    
def print_results(c_result: np.ndarray, m_result: np.ndarray, e_result: np.ndarray) -> None:
    """
    Neatly prints results of all calculations

    Args:
        c_result (np.ndarray): Result from calculate_result()
        m_result (np.ndarray): Result using Numpy's matmul()
        e_result (np.ndarray): Result using Numpy's einsum()
    """
    # Print results
    print("calculate_result() = %s\n" % c_result)
    print("Matmul Result = %s\n" % m_result)
    print("Einsum Result = %s\n" % e_result)
    
    # Confirm matmul and einsum results are equal since they're both the correct result
    if not np.array_equal(m_result, e_result):
        print("Matmul and einsum results are supposed to be equal. Something is very wrong here...\n")
        exit(0)
         
if __name__ == "__main__":
    # Generate random matrix of size LENGTH * LENGTH
    rand_mat1 = np.random.randint(MIN, MAX, size = (LENGTH, LENGTH))
    print("Random Matrix #1 = %s\n" % rand_mat1)
    
    # Generate random vector of size LENGTH
    rand_mat2 = np.random.randint(MIN, MAX, size = LENGTH)
    print("Random Matrix #2 = %s\n" % rand_mat2)
                
    # Calculate threaded result
    c_result = calculate_result(rand_mat1, rand_mat2)

    # Print c_results for debugging
    print("\ncalculate_result(Random Matrix #1, Random Matrix #2) = %s" % c_result)
    
    # Calculate correct result using matmul
    m_result = rand_mat1 @ rand_mat2
    
    # Calculate correct result using einsum
    #e_result = np.einsum('ij,j->i', rand_mat1, rand_mat2)
    
    # Print results
    #print_results(c_result, m_result, e_result)
    
    # Simulate calculations
    #simulations()

    # Check if result is correct
    if np.array_equal(m_result, c_result):
        print("\nCorrect Calculation!")
        exit(1)
    else:
        print("\nIncorrect Calculation...")
        exit(0)