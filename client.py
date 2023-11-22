from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, error
from pickle import loads, dumps
from numpy import ndarray, random, array_split, array_equal, concatenate
from queue import Queue

HOST = "127.0.0.1"
PORTS = [12345, 12346, 12347]
BUFFER = 4096
LENGTH = 128
MATRIX_2_WIDTH = 2
HORIZONTAL_PARTITIONS = 16
VERTICAL_PARTITIONS = 16
MIN = 0
MAX = 5
TIMEOUT = 10
HEADERSIZE = 10

# TODO Partition formula?

class Client():
    def __init__(self, matrix_a: ndarray, matrix_b: ndarray, host: str = HOST, ports: list[int] = PORTS):
        # IP Address
        self._host: str = host

        # List of port(s) (i.e. server(s))
        self._ports: list[int] = ports

        # Queue of partitions of Matrix A and Matrix B and their position, to be sent to server(s)
        self._partitions: Queue = Client.queue_partitions(self, matrix_a, matrix_b)

        # Dictionary to store results from server(s) (i.e. Value = Chunk of Matrix A * Chunk of Matrix B at Key = given position)
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
        # Declare queue to be populated and returned
        queue = Queue()

        # Get partitions of Matrix A and Matrix B
        matrix_a_partitions, matrix_b_partitions = Client.partition_m1(self, matrix_a), Client.partition_m2(self, matrix_b)

        # Add partitions of Matrix A and Matrix B and their position to queue
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
        # Send partitioned matrices to server(s)
        Client.send_matrices(self)

        # Return [all] results combined into a single matrix
        return Client.combine_results(self)

    def combine_results(self) -> ndarray:
        """
        Combines all separate submatrices into a single matrix

        Returns:
            ndarray: Combined result of given matrices
        """
        # Declare list for storing combined results, and end index
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
        Send partitioned matrices to server(s)
        """
        # Index used to determine which server to connect to (i.e. cycles through each server; round robin)
        i = 0

        # While there's still partitions to send to server(s)
        while not self._partitions.empty():
            try:
                with socket(AF_INET, SOCK_STREAM) as sock:
                    # Allow reuse of address
                    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

                    # Address of server
                    address = (self._host, self._ports[i % len(self._ports)])

                    # Connect to server
                    sock.connect(address)

                    # Get partitions to send to server
                    to_send = dumps(self._partitions.get())

                    # Add header to partitions
                    to_send = bytes(f"{len(to_send):<{HEADERSIZE}}", "utf-8") + to_send

                    # Send partitions to server
                    #print(f"Sending {to_send} from {sock.getsockname()}\n")
                    sock.sendall(to_send)
                    #sock.send(dumps(to_send))

                    # Receive acknowledgment from the server
                    ack_data = sock.recv(HEADERSIZE)
                    ack_msg_length = int(ack_data.decode("utf-8").strip())

                    # Ensure the acknowledgment is "ACK"
                    ack_msg = sock.recv(ack_msg_length).decode("utf-8").strip()
                    if ack_msg != "ACK":
                        raise ValueError(f"Invalid acknowledgment: {ack_msg}")

                    # Receive the result matrix
                    data = b""
                    new_data = True
                    msg_length = 0
                    
                    while True:
                        packet = sock.recv(BUFFER)
                        if not packet:
                            break
                        data += packet

                        # Check if the entire message has been received
                        if new_data:
                            msg_length = int(data[:HEADERSIZE])
                            new_data = False

                        if len(data) - HEADERSIZE >= msg_length:
                            break

                    # Receive result (i.e. product of partitions and its position) from server
                    result, index = loads(data[HEADERSIZE:HEADERSIZE + msg_length]) #loads(sock.recv(BUFFER))
                    #print(f"Received [{index}]: {result} from ({address})\n")

                    # Add result to dict, to be combined into final result later
                    self._matrix_products[index] = result

                    # Increment index
                    i += 1

            # Catch exception
            except error as msg:
                print(f"ERROR: {msg}")
                exit(1)

def verify(result: ndarray, check: ndarray) -> bool:
    """
    Checks if result is correct

    Args:
        result (ndarray): Calculated result
        check (ndarray): Numpy's result

    Returns:
        bool: True if correct, False otherwise
    """
    return array_equal(result, check)

def generate_matrix(length: int, width: int) -> ndarray:
    """
    Generates a random matrix of size length * width

    Args:
        length (int): Length of matrix
        width (int): Width of matrix

    Returns:
        ndarray: Random matrix of size length * width
    """
    return random.randint(MIN, MAX, size = (length, width))

def print_outcome(result: ndarray, check: ndarray) -> None:
    """
    Prints calculation's outcome (i.e. correctness)

    Args:
        result (ndarray): Calculated result
        check (ndarray): Numpy's result
    """
    if verify(result, check):
        print("CORRECT CALCULATION!")
        exit(0)

    else:
        print("INCORRECT CALCULATION...")
        exit(1)

if __name__ == "__main__":
    # Generate example matrices for testing
    matrix_a = generate_matrix(LENGTH, LENGTH)
    matrix_b = generate_matrix(LENGTH, MATRIX_2_WIDTH)

    # Create Client to multiply matrices
    client = Client(matrix_a, matrix_b)

    # Get result
    answer = client.get_result()
    #print(f"Calculated: {answer}\n")

    # Get correct answer
    correct_answer = matrix_a @ matrix_b

    # Print outcome (i.e. answer's correctness)
    print_outcome(answer, correct_answer)