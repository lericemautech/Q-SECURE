from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, error
from pickle import loads, dumps
from numpy import ndarray, random, array_split, array_equal, concatenate
from queue import Queue
from random import sample
from Shared import Address, HEADERSIZE, LENGTH, MATRIX_2_WIDTH, HORIZONTAL_PARTITIONS, VERTICAL_PARTITIONS, receive, send, generate_matrix

#ADDRESSES = [ Address("127.0.0.1", 12345), Address("127.0.0.1", 12346), Address("127.0.0.1", 12347) ]
ADDRESSES = [ Address("192.168.207.129", 12345), Address("192.168.207.130", 12346), Address("192.168.207.131", 12347) ]
# VM1/Client, VM2/Server, VM3/Server

class Client():
    def __init__(self, matrix_a: ndarray, matrix_b: ndarray, addresses: list[Address] = ADDRESSES):
        # IP Address(es) and ports of server(s)
        self._addresses: list[Address] = addresses
        
        # Queue of partitions of Matrix A and Matrix B and their position, to be sent to server(s)
        self._partitions: Queue = self._queue_partitions(matrix_a, matrix_b)

        # Dictionary to store results from server(s) (i.e. Value = Chunk of Matrix A * Chunk of Matrix B at Key = given position)
        self._matrix_products: dict[int, ndarray] = { }

    def _partition(self, matrix_a: ndarray, matrix_b: ndarray) -> tuple[list[ndarray], list[ndarray]]:
        """
        Partition Matrix A and Matrix B into submatrices

        Args:
            matrix_a (ndarray): Matrix A to be partitioned
            matrix_b (ndarray): Matrix B to be partitioned

        Returns:
            tuple[list[ndarray], list[ndarray]]: Partitioned Matrix A and Matrix B
        """
        # Split matrix horizontally
        sub_matrices = array_split(matrix_a, HORIZONTAL_PARTITIONS, axis = 0)
        
        # Split submatrices vertically, then return
        return [m for sub_matrix in sub_matrices for m in  array_split(sub_matrix, VERTICAL_PARTITIONS, axis = 1)], array_split(matrix_b, VERTICAL_PARTITIONS, axis = 0)

    def _queue_partitions(self, matrix_a: ndarray, matrix_b: ndarray) -> Queue:
        """
        Add partitions of Matrix A and Matrix B and their position to queue

        Args:
            matrix_a (ndarray): Matrix A
            matrix_b (ndarray): Matrix B

        Returns:
            Queue: Queue of partitions of Matrix A and Matrix B and their position
        """
        # Declare queue to be populated and returned
        queue = Queue()

        # Get partitions of Matrix A and Matrix B
        matrix_a_partitions, matrix_b_partitions = self._partition(matrix_a, matrix_b)

        # Add partitions of Matrix A and Matrix B and their position to queue
        for i in range(len(matrix_a_partitions)):
            queue.put((matrix_a_partitions[i], matrix_b_partitions[i % VERTICAL_PARTITIONS], i))

        return queue

    def _combine_results(self, matrix_products: dict[int, ndarray]) -> ndarray:
        """
        Combines all separate submatrices into a single matrix

        Args:
            matrix_products (dict[int, ndarray]): Dictionary to store results (i.e. Value = Chunk of Matrix A * Chunk of Matrix B at Key = given position)

        Returns:
            ndarray: Combined result of given matrices
        """
        # Declare list for storing combined results, and end index
        combined_results, end = [], 0

        # Get all results from the queue, sorted by its position
        results = [value for _, value in sorted(matrix_products.items())]

        # Sum all values in the same row, then add to combined_results
        for i in range(0, len(results), VERTICAL_PARTITIONS):
            end += VERTICAL_PARTITIONS
            combined_results.append(sum(results[i:end]))

        # Combine all results into a single matrix
        return concatenate(combined_results)

    def get_result(self) -> ndarray:
        """
        Use client and server to multiply matrices, then get result

        Returns:
            ndarray: Product of Matrix A and Matrix B 
        """
        select = random.randint(1, len(self._addresses) + 1)
        print("Generated Number =", select)
        
        # Send partitioned matrices to 2 randomly selected server(s)
        self._work(select)

        # Return [all] results combined into a single matrix
        return self._combine_results(self._matrix_products)

    def _handle_server(self, client_socket: socket, data: bytes) -> bytes:
        """
        Exchange data with server

        Args:
            client_socket (socket): Client socket
            data (bytes): Data to be sent

        Raises:
            ValueError: Invalid acknowledgment (i.e. "ACK" not received from server)

        Returns:
            bytes: Data received from server
        """
        try:
            # Add header to and send data packet to server
            send(client_socket, data)

            # Receive acknowledgment from server
            ack_data = client_socket.recv(HEADERSIZE)

            # Verify acknowledgment
            ack_msg_length = int(ack_data.decode("utf-8").strip())
            ack_msg = client_socket.recv(ack_msg_length).decode("utf-8").strip()
            if ack_msg != "ACK":
                raise ValueError(f"Invalid acknowledgment: {ack_msg}")
                                
            # Receive data from server
            return receive(client_socket)

        # Catch exceptions
        except ConnectionRefusedError:
            print("ERROR: (Client._handle_server) Connection to server refused")
            exit(1)
            
        except ConnectionError:
            print("ERROR: (Client._handle_server) Connection to server lost")
            exit(1)
                
        except error as msg:
            print(f"ERROR: (Client._handle_server) {msg}")
            exit(1)

    def _select_servers(self, num_servers: int) -> list[Address]:
        """
        Selects a random subset of server(s) to send jobs to

        Args:
            num_servers (int): Amount of servers to send jobs to

        Returns:
            list[Address]: List of randomly selected server addresses to send jobs to
        """
        if num_servers > len(self._addresses):
            raise ValueError(f"ERROR: Number of servers ({num_servers}) exceeds number of addresses ({len(self._addresses)})")

        return sample(self._addresses, num_servers)

    def _work(self, num_servers: int) -> None:
        """
        Send partitioned matrices to server(s), get results,
        then add them to dictionary for combining laters

        Args:
            num_servers (int): Amount of servers to send jobs tos
        """
        # Index used to determine where to connect (i.e. cycles through available servers; round robin)
        i = 0

        # Select random subset of server(s) to send jobs to
        server_addresses = self._select_servers(num_servers)

        # While there's still partitions to send to server(s)
        while not self._partitions.empty():
            try:
                with socket(AF_INET, SOCK_STREAM) as client_socket:
                    # Allow reuse of address
                    client_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

                    # Address of server
                    server_address = server_addresses[i % len(server_addresses)]

                    # Connect to server
                    client_socket.connect(server_address)
 
                    # Get partitions to send to server
                    partitions = self._partitions.get()

                    # Receive result from server
                    data = self._handle_server(client_socket, dumps(partitions))
                    
                    # Unpack data (i.e. product of partitions and its position) from server
                    result, index = loads(data)

                    # Check if result and index was received (i.e. not None)
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

            # Catch exceptions
            except ConnectionRefusedError:
                print("ERROR: (Client._work) Connection to server refused")
                exit(1)

            except ConnectionError:
                print("ERROR: (Client._work) Connection to server lost")
                exit(1)
            
            except error as msg:
                print(f"ERROR: (Client._work) {msg}")
                exit(1)

def print_outcome(result: ndarray, check: ndarray) -> None:
    """
    Prints calculation's outcome (i.e. correctness)

    Args:
        result (ndarray): Calculated result
        check (ndarray): Numpy's result
    """
    if array_equal(result, check):
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

    # Print outcome (i.e. answer's correctness)
    print_outcome(answer, matrix_a @ matrix_b)
