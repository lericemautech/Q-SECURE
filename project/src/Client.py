from socket import socket, error, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from pickle import loads, dumps
from numpy import ndarray, random, array_equal, concatenate, dot, shape
from queue import Queue
from os import path
from random import sample
from time import perf_counter
from logging import getLogger, shutdown
from logging.config import fileConfig
from project.src.Shared import Address, receive, send, generate_matrix, partition, DIRECTORY_PATH, FILENAME, HEADERSIZE, LENGTH, LOG_CONF_PATH

MATRIX_2_WIDTH = 2
SIG_FIGS = 5
CLIENT_LOGFILE = "client.log"
CLIENT_LOGGER = getLogger(__name__)
# TODO Relocate ADDRESSES to separate file for improved security and editing
ADDRESSES = [ Address("127.0.0.1", 12345), Address("127.0.0.1", 12346), Address("127.0.0.1", 12347) ]
#ADDRESSES = [ Address("192.168.207.129", 12345), Address("192.168.207.130", 12346), Address("192.168.207.131", 12347) ]

class Client():
    def __init__(self, matrix_a: ndarray, matrix_b: ndarray, addresses: list[Address] = ADDRESSES):
        # Store server(s) results (i.e. Value = Chunk of Matrix A * Chunk of Matrix B at Key = given position)
        self._matrix_products: dict[int, ndarray] = { }

        # Select random number N between 1 and # of Servers, inclusive
        self._num_servers: int = random.randint(1, len(addresses) + 1)

        # Select random subset of server(s) to send jobs to        
        self._server_addresses: list[Address] = self._select_servers(addresses, self._num_servers)
        
        # Queue of partitions of Matrix A and Matrix B and their position, to be sent to selected server(s)
        self._partitions: Queue = self._queue_partitions(matrix_a, matrix_b)

        # Determine which selected server(s) to send jobs to; initialize all selected server(s) with 0 points
        self._server_reliability: dict[Address, int] = { address: 0 for address in self._server_addresses }

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
        matrix_a_partitions, matrix_b_partitions = partition(matrix_a, matrix_b)

        # Add partitions of Matrix A and Matrix B and their position to queue
        for i in range(len(matrix_a_partitions)):
            # Have client compute some of the partitions; add 1 to num_servers to account for client
            if i % (self._num_servers + 1) == 0:
                self._matrix_products[i] = dot(matrix_a_partitions[i], matrix_b_partitions[i % len(matrix_b_partitions)])

            # ...while server(s) compute the rest
            else:
                queue.put((matrix_a_partitions[i], matrix_b_partitions[i % len(matrix_b_partitions)], i))

        return queue

    def _combine_results(self, matrix_products: dict[int, ndarray]) -> ndarray:
        """
        Combines all separate submatrices into a single matrix

        Args:
            matrix_products (dict[int, ndarray]): Dictionary to store results (i.e. Value = Chunk of Matrix A * Chunk of Matrix B at Key = given position)

        Returns:
            ndarray: Combined result of given matrices
        """
        # Get all results from the queue, sorted by its position
        results = [value for _, value in sorted(matrix_products.items())]

        # Number of columns, end index, and list for storing combined results
        num_columns, end, combined_results = shape(results[0])[1], 0, []

        # Sum all values in the same row, then add to combined_results
        for i in range(0, len(results), num_columns):
            end += num_columns
            combined_results.append(sum(results[i:end]))

        # Combine all results into a single matrix
        return concatenate(combined_results)

    def get_result(self) -> ndarray:
        """
        Use client and server to multiply matrices, then get result

        Returns:
            ndarray: Product of Matrix A and Matrix B 
        """
        CLIENT_LOGGER.info(f"Generated number of servers to send jobs to = {self._num_servers}\n")
        
        # Send partitioned matrices to randomly selected server(s)
        self._work()

        # Return [all] results combined into a single matrix
        return self._combine_results(self._matrix_products)        

    def _handle_server(self, server_socket: socket, data: bytes) -> bytes:
        """
        Exchange data with server

        Args:
            server_socket (socket): Server socket
            data (bytes): Data to be sent

        Raises:
            ValueError: Invalid acknowledgment

        Returns:
            bytes: Data received from server
        """
        # Add header to and send data packet to server
        send(server_socket, data)

        # Receive acknowledgment from server
        ack_data = server_socket.recv(HEADERSIZE)

        # Verify acknowledgment
        ack_msg_length = int(ack_data.decode("utf-8").strip())
        ack_msg = server_socket.recv(ack_msg_length).decode("utf-8").strip()
        if ack_msg != "ACK":
            exception_msg = f"(Client._handle_server) Invalid acknowledgment \"{ack_msg}\""
            CLIENT_LOGGER.exception(exception_msg)
            shutdown()
            raise ValueError(exception_msg) from None
                            
        # Receive data from server
        return receive(server_socket)

    def _select_servers(self, addresses: list[Address], num_servers: int) -> list[Address]:
        """
        Selects a subset of server(s) with the highest compute power (i.e. most CPUs) to send jobs to

        Args:
            addresses (list[Address]): List of server addresses
            num_servers (int): Amount of servers to send jobs to

        Raises:
            ValueError: Invalid number of servers
            FileNotFoundError: File containing server information does not exist
            IOError: File containing server information is empty
            
        Returns:
            list[Address]: List of server addresses to send jobs to
        """
        # TODO
        selected_servers = { }
        
        if num_servers > len(addresses) or num_servers < 1:
            exception_msg = f"(Client._select_servers) {num_servers} is an invalid number of servers"
            CLIENT_LOGGER.exception(exception_msg)
            raise ValueError(exception_msg) from None

        filepath = path.join(DIRECTORY_PATH, FILENAME)

        if not path.exists(filepath):
            exception_msg = f"(Client._select_servers) File {FILENAME} at {DIRECTORY_PATH} does not exist"
            CLIENT_LOGGER.exception(exception_msg)
            shutdown()
            raise FileNotFoundError(exception_msg) from None

        if path.getsize(filepath) == 0:
            exception_msg = f"(Client._select_servers) File {FILENAME} at {DIRECTORY_PATH} is empty"
            CLIENT_LOGGER.exception(exception_msg)
            shutdown()
            raise IOError(exception_msg) from None

        # Read file containing server addresses and their CPU
        with open(filepath, "r") as file:
            for line in file:
                # Get IP Address, port, and CPU of server
                curr_ip, curr_port, curr_cpu = line.split(" ")[:3]
                curr_address = Address(curr_ip, int(curr_port))

                # Add server address and CPU to dict if not already in it
                if curr_address not in selected_servers.keys():
                    selected_servers[curr_address] = int(curr_cpu)

        # Check if all selected servers have the same CPU power
        if len(set(selected_servers.values())) == 1:
            # If so, choose randomly from selected servers
            return sample(list(selected_servers.keys()), num_servers)

        # Otherwise, return the top servers (i.e. servers with highest CPU power)
        return sorted(selected_servers, reverse = True)[:num_servers]

    def _work(self) -> None:
        """
        Send partitioned matrices to server(s), get results,
        then add them to dictionary for combining laters

        Raises:
            BrokenPipeError: Unable to write to shutdown socket
            ConnectionRefusedError: Connection refused
            ConnectionAbortedError: Connection aborted
            ConnectionResetError: Connection reset
            ConnectionError: Connection lost
            TimeoutError: Connection timed out
        """
        # Index used to determine where to connect (i.e. cycles through available servers; round robin)
        i = 0

        # While there's still partitions to send to server(s)
        while not self._partitions.empty():
            try:
                with socket(AF_INET, SOCK_STREAM) as client_socket:
                    # Allow reuse of address
                    client_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

                    # Address of server
                    server_address = self._server_addresses[i % len(self._server_addresses)]

                    # Start timer
                    start = perf_counter()

                    # Connect to server
                    client_socket.connect(server_address)

                    # Get partitions to send to server
                    partitions = self._partitions.get(timeout = 0.1)

                    # Receive result from server
                    data = self._handle_server(client_socket, dumps(partitions))
                    
                    # Unpack data (i.e. product of partitions and its position) from server
                    result, index = loads(data)

                    # End timer
                    end = perf_counter()

                    CLIENT_LOGGER.info(f"Took Client {round(end - start, SIG_FIGS)} seconds to send and receive data from Server at {server_address}")

                    # Check if result and index was received (i.e. not None)
                    if result is not None:
                        #print(f"Result Matrix from Server at {server_address} = {result}\n")

                        # Add result to dict, to be combined into final result later
                        self._matrix_products[index] = result

                        # Increase server's reliability
                        self._server_reliability[server_address] += 1

                    else:
                        CLIENT_LOGGER.error(f"Failed to receive valid result from Server at {server_address}; retrying later...")

                        # Put partitions back into queue (since it was previously removed via .get()), to try again later
                        self._partitions.put(partitions)

                        # Decrease server's reliability
                        self._server_reliability[server_address] -= 1

                    CLIENT_LOGGER.info(f"Server at {server_address} has {self._server_reliability[server_address]} points")

                    # Increment index
                    i += 1

            except BrokenPipeError:
                exception_msg = "(Client._work) Unable to write to shutdown socket"
                CLIENT_LOGGER.exception(exception_msg)
                shutdown()
                raise BrokenPipeError(exception_msg) from None

            except ConnectionRefusedError:
                exception_msg = "(Client._work) Connection refused"
                CLIENT_LOGGER.exception(exception_msg)
                shutdown()
                raise ConnectionRefusedError(exception_msg) from None

            except ConnectionAbortedError:
                exception_msg = "(Client._work) Connection aborted"
                CLIENT_LOGGER.exception(exception_msg)
                shutdown()
                raise ConnectionAbortedError(exception_msg) from None

            except ConnectionResetError:
                exception_msg = "(Client._work) Connection reset"
                CLIENT_LOGGER.exception(exception_msg)
                shutdown()
                raise ConnectionResetError(exception_msg) from None

            except ConnectionError:
                exception_msg = "(Client._work) Connection lost"
                CLIENT_LOGGER.exception(exception_msg)
                shutdown()
                raise ConnectionError(exception_msg) from None

            except TimeoutError:
                exception_msg = "(Client._work) Connection timed out"
                CLIENT_LOGGER.exception(exception_msg)
                shutdown()
                raise TimeoutError(exception_msg) from None

            except error as msg:
                CLIENT_LOGGER.exception(f"(Client._work) {msg}")
                shutdown()
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
        shutdown()
        exit(0)

    else:
        print("INCORRECT CALCULATION...")
        shutdown()
        exit(1)

if __name__ == "__main__":
    # Logging
    fileConfig(LOG_CONF_PATH, defaults = { "logfilename" : CLIENT_LOGFILE}, disable_existing_loggers = False)
    CLIENT_LOGGER.info("Client started")
    
    # Generate example matrices for testing
    matrix_a = generate_matrix(LENGTH, LENGTH)
    matrix_b = generate_matrix(LENGTH, MATRIX_2_WIDTH)

    print(f"Matrix A: {matrix_a}\n")
    print(f"Matrix B: {matrix_b}\n")

    # Create Client to multiply matrices
    client = Client(matrix_a, matrix_b)

    # Start timer
    start = perf_counter()

    # Get result
    answer = client.get_result()
    CLIENT_LOGGER.info(f"Took {round(perf_counter() - start, SIG_FIGS)} seconds to get result")
    print(f"Final Result Matrix = {answer}\n")

    # Print outcome (i.e. answer's correctness)
    print_outcome(answer, matrix_a @ matrix_b)
