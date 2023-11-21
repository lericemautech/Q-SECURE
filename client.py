from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, error
from pickle import loads, dumps
from numpy import ndarray, random, array_split, array_equal, concatenate
from queue import Queue

# get small matrix client
# call func to partition in main

HOST = "127.0.0.1"
PORTS = [12345, 12346]
BUFFER = 2048
LENGTH = 8
MATRIX_2_WIDTH = 2
HORIZONTAL_PARTITIONS = 2
VERTICAL_PARTITIONS = 2
MIN = 0
MAX = 5
TIMEOUT = 10

class Client():
    def __init__(self, matrix_a: ndarray, matrix_b: ndarray, host: str = HOST, ports: list[int] = PORTS):
        self._host: str = host
        self._ports: list[int] = ports
        self._partitions: Queue = Client.queue_partitions(self, matrix_a, matrix_b)
        self._matrix_products: dict = { }

    def queue_partitions(self, matrix_a: ndarray, matrix_b: ndarray) -> Queue:
        """
        Add partitions of Matrix A and Matrix B and their position to queue

        Args:
            matrix_a (ndarray): Matrix #1
            matrix_b (ndarray): Matrix #2

        Returns:
            Queue: Queue of partitions of Matrix A and Matrix B and their position
        """
        queue, matrix_a_partitions, matrix_b_partitions = Queue(), Client.partition_m1(self, matrix_a), Client.partition_m2(self, matrix_b)

        for i in range(len(matrix_a_partitions)):
            queue.put((matrix_a_partitions[i], matrix_b_partitions[i % VERTICAL_PARTITIONS], i))

        return queue

    def partition_m1(self, matrix: ndarray) -> list:
        """
        Partition Matrix #1 into submatrices

        Args:
            matrix (ndarray): Matrix #1 to be partitioned

        Returns:
            list: Partitioned Matrix #1
        """
        # Check if matrix is 1D (i.e. vector)
        if matrix.ndim == 1: return Client.partition_m2(self, matrix)
        
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

    def get_result(self) -> ndarray:
        """
        Use client and server to multiply matrices, then get result

        Returns:
            ndarray: Product of Matrix A and Matrix B 
        """
        Client.send_matrices(self)
        
        return Client.combine_results(self)

    def combine_results(self) -> ndarray:
        """
        Combines all separate submatrices into a single matrix

        Returns:
            ndarray: Combined result of given matrices
        """
        combined_results, end = [], 0

        # Get all results from the queue, sorted by its position
        results = [value for _, value in sorted(self._matrix_products.items())]

        # Sum all values in the same row, then add to combined_results
        for i in range(0, len(results), VERTICAL_PARTITIONS):
            end += VERTICAL_PARTITIONS
            combined_results.append(sum(results[i:end]))

        # Combine all results into a single matrix
        return concatenate(combined_results)
    
    def send_matrices(self) -> None:
        """
        Sends partitioned matrices to server(s)
        """
        i = 0
        
        try:                
            while not self._partitions.empty():
                with socket(AF_INET, SOCK_STREAM) as sock:
                    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
                    sock.connect((self._host, self._ports[i % len(self._ports)]))
                    to_send = self._partitions.get()
                    print(f"Sending {to_send} to {sock.getsockname()}")
                    sock.sendall(dumps(to_send))
                    result, index = loads(sock.recv(BUFFER))
                    self._matrix_products[index] = result
                    i += 1
            
        except error as msg:
            print("ERROR: %s\n" % msg)
            exit(0)

if __name__ == "__main__":
    # Example matrices for testing
    matrix_a = random.randint(MIN, MAX, size = (LENGTH, LENGTH))
    matrix_b = random.randint(MIN, MAX, size = (LENGTH, MATRIX_2_WIDTH))

    client = Client(matrix_a, matrix_b)

    answer = client.get_result()

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