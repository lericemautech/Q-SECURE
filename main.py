from numpy import ndarray
from Manager import Manager
from Shared import print_outcome, generate_matrix, LENGTH, MATRIX_2_WIDTH

def calculate_result(matrix_1: ndarray, matrix_2: ndarray) -> ndarray:
    """
    Matrix multiplication using threads and partitioning

    Args:
        matrix_1 (ndarray): Matrix #1 with length and width = LENGTH
        matrix_2 (ndarray): Matrix #2 with length = LENGTH

    Returns:
        ndarray: Result of multiplying Matrix #1 and Matrix #2
    """
    # Create Manager to multiply the matrices with multiprocessing
    manager = Manager(matrix_1, matrix_2)

    return manager.get_result()
    
def print_results(c_result: ndarray, m_result: ndarray, e_result: ndarray) -> None:
    """
    Neatly prints results of all calculations

    Args:
        c_result (ndarray): Result from calculate_result()
        m_result (ndarray): Result from matmul()
        e_result (ndarray): Result from einsum()
    """
    # Print results
    print("calculate_result() = %s" % c_result)
    print("matmul() = %s" % m_result)
    print("einsum() = %s\n" % e_result)
         
if __name__ == "__main__":
    # Generate random matrix of size LENGTH * LENGTH
    rand_mat1 = generate_matrix(LENGTH, LENGTH)
        
    # Generate random matrix of size LENGTH * MATRIX_2_WIDTH
    rand_mat2 = generate_matrix(LENGTH, MATRIX_2_WIDTH)
                
    # Calculate threaded result
    c_result = calculate_result(rand_mat1, rand_mat2)
        
    # Calculate correct result using matmul
    m_result = rand_mat1 @ rand_mat2
    
    # Calculate correct result using einsum
    #e_result = np.einsum('ij,j->i', rand_mat1, rand_mat2)
    
    # Print results
    #print_results(c_result, m_result, e_result)

    # Print outcome
    print_outcome(c_result, m_result)