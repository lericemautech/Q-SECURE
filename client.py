from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, error
from pickle import loads, dumps
from numpy import ndarray, random, array_split, array_equal
from queue import Queue
from random import sample
from Shared import HOST, PORTS, HEADERSIZE, TIMEOUT, LENGTH, MATRIX_2_WIDTH, HORIZONTAL_PARTITIONS, VERTICAL_PARTITIONS, receive_data, add_header, generate_matrix, combine_results

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
        select = random.randint(1, len(self._ports) + 1)
        print("Generated Number =", select)
        
        # Send partitioned matrices to 2 randomly selected server(s)
        Client.work(self, select)

        # Return [all] results combined into a single matrix
        return combine_results(self._matrix_products)

    def select_servers(self, num_servers: int) -> list[int]:
        """
        Selects a random subset of server(s) to send jobs to

        Args:
            num_servers (int): Amount of servers to send jobs to

        Returns:
            list[int]: List of randomly selected server ports to send jobs to
        """
        if num_servers > len(self._ports):
            raise ValueError(f"ERROR: Number of servers ({num_servers}) exceeds number of ports ({len(self._ports)})")

        return sample(self._ports, num_servers)
    
    def work(self, num_servers: int) -> None:
        """
        Send partitioned matrices to server(s), get results,
        then add them to dictionary for combining laters

        Args:
            num_servers (int): Amount of servers to send jobs tos
        """
        # Index used to determine where to connect (i.e. cycles through available servers; round robin)
        i = 0

        # Select random server(s) to send jobs to
        server_addresses = Client.select_servers(self, num_servers)

        # While there's still partitions to send to server(s)
        while not self._partitions.empty():
            try:
                with socket(AF_INET, SOCK_STREAM) as client_socket:
                    # Allow reuse of address
                    client_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

                    # Set socket's timeout
                    #client_socket.settimeout(TIMEOUT)

                    # Address of server
                    server_address = (self._host, server_addresses[i % len(server_addresses)])

                    # Connect to server
                    client_socket.connect(server_address)
 
                    # Get partitions to send to server
                    partitions = self._partitions.get()

                    # Convert partitions to bytes
                    to_send = dumps(partitions)

                    # Add header to partitions packet
                    to_send = add_header(to_send)

                    # Send partitions to server
                    client_socket.sendall(to_send)
                    #print("Sent:", partitions)

                    # Receive acknowledgment from server
                    ack_data = client_socket.recv(HEADERSIZE)

                    # Verify acknowledgment
                    ack_msg_length = int(ack_data.decode("utf-8").strip())
                    ack_msg = client_socket.recv(ack_msg_length).decode("utf-8").strip()
                    if ack_msg != "ACK":
                        raise ValueError(f"Invalid acknowledgment: {ack_msg}")
                                        
                    # Receive result from server
                    data = receive_data(client_socket)
                    
                    # Unpack data (i.e. product of partitions and its position) from server
                    result, index = loads(data)

                    if result is not None:
                        print(f"Result Matrix from Server at {server_address} = {result}\n")

                        # Add result to dict, to be combined into final result later
                        self._matrix_products[index] = result

                    else:
                        print(f"Failed to receive result from Server at {server_address}; retrying later...\n")

                        # Put partitions back into queue (since it was previously removed via .get()), to try again later
                        self._partitions.put(partitions)

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

    #print(f"Matrix A: {matrix_a}\n")
    #print(f"Matrix B: {matrix_b}\n")

    # Create Client to multiply matrices
    client = Client(matrix_a, matrix_b)

    # Get result
    answer = client.get_result()
    print(f"Final Result Matrix = {answer}\n")

    # Get correct answer
    correct_answer = matrix_a @ matrix_b

    # Print outcome (i.e. answer's correctness)
    print_outcome(answer, correct_answer)