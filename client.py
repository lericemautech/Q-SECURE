from socket import socket, AF_INET, SOCK_STREAM, error
from pickle import loads, dumps
from numpy import ndarray, random, array_split, array_equal, concatenate

# get small matrix client
# call func to partition in main

HOST = "127.0.0.1"
PORT = 12345
BUFFER = 4096
LENGTH = 8
HORIZONTAL_PARTITIONS = 2
VERTICAL_PARTITIONS = 2
MIN = 0
MAX = 5

def partition(matrix: ndarray) -> list:
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
    
    # Split submatrices vertically, then return
    return [m for sub_matrix in sub_matrices for m in  array_split(sub_matrix, VERTICAL_PARTITIONS, axis = 1)]

def combine_results(matrices: dict) -> ndarray:
    """
    Combines all separate submatrices into a single matrix

    Args:
        matrices (dict): Results of each partitioned matrices' multiple

    Returns:
        ndarray: Combined result of given matrices
    """
    combined_results, end = [], 0

    # Get all results from the queue, sorted by its position
    results = [value for _, value in sorted(matrices.items())]

    # Sum all values in the same row, then add to combined_results
    for i in range(0, len(results), VERTICAL_PARTITIONS):
        end += VERTICAL_PARTITIONS
        combined_results.append(sum(results[i:end]))

    # Combine all results into a single matrix
    return concatenate(combined_results)

def send_matrices(server_address: tuple[str, int], matrix_a_partitions: list, matrix_b_partitions: list) -> dict:
    """
    Sends partitioned matrices to server

    Args:
        server_address (tuple[str, int]): Server's IP address and port number
        matrix_a_partitions (list): Matrix A's partitions
        matrix_b_partitions (list): Matrix B's partitions

    Returns:
        dict: Results of each partitioned matrices' multiple
    """
    results = [ ]
    client_socket = socket(AF_INET, SOCK_STREAM)
    
    try:
        client_socket.connect(server_address)
        matrices = {'matrix_a': matrix_a_partitions, 'matrix_b': matrix_b_partitions}
        client_socket.send(dumps(matrices))
        data = client_socket.recv(BUFFER)
        results = loads(data)
        client_socket.close()
        return results

    except error as msg:
        client_socket.close()
        print("ERROR: %s\n" % msg)
        exit(1)

if __name__ == "__main__":
    # Example matrices for testing
    matrix_a = random.randint(MIN, MAX, size = (LENGTH, LENGTH))
    matrix_b = random.randint(MIN, MAX, size = LENGTH)

    matrix_a_partitions = partition(matrix_a)
    matrix_b_partitions = partition(matrix_b)

    server_address = (HOST, PORT)
    result = send_matrices(server_address, matrix_a_partitions, matrix_b_partitions)
    answer = combine_results(result)

    print("Matrix A:")
    print(matrix_a)
    print("\nMatrix B:")
    print(matrix_b)
    print("\nResult Matrix:")
    print(answer)

    print("\nCorrect answer:", matrix_a @ matrix_b)

    if array_equal(matrix_a @ matrix_b, answer):
        print("\nSuccess!")
    else: print("\nFailure!")