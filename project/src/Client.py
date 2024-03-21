from collections.abc import Iterator
from socket import socket, error, SOL_SOCKET, SO_REUSEADDR
from errno import EADDRINUSE, EADDRNOTAVAIL
from pickle import loads, dumps
from numpy import ndarray, random, array_split, concatenate, dot, shape, array_equal
from queue import Queue
from os import path, SEEK_END
from random import sample
from time import perf_counter
from logging import getLogger, shutdown
from sympy import IndexedBase, Matrix, matrix2numpy
from project.src.ExceptionHandler import handle_exceptions
from project.src.Shared import (Address, ACKNOWLEDGEMENT, HORIZONTAL_PARTITIONS,
                                SERVER_INFO_PATH, HEADERSIZE, LENGTH, VERTICAL_PARTITIONS,
                                create_logger, receive, send, generate_matrix, timing)

MATRIX_B_WIDTH = 2
"""Matrix B's width"""

X = IndexedBase("x")
"""Base of subscriptable variable used to replace elements in matrix"""

CLIENT_LOGGER = getLogger(__name__)
"""Client logger"""

# TODO Implement load balancer for client-servers
# TODO Pyfhel Client-Server demo
# https://pyfhel.readthedocs.io/en/latest/_autoexamples/Demo_5_CS_Client.html#sphx-glr-autoexamples-demo-5-cs-client-py

class Client():
    def __init__(self, matrix_a: ndarray, matrix_b: ndarray):
        create_logger("client.log")
        CLIENT_LOGGER.info("Starting Client...\n")

        # Ensure Matrix B's width is not smaller than number of vertical partitions
        if MATRIX_B_WIDTH < VERTICAL_PARTITIONS:
            exception_msg = f"Matrix B's width ({MATRIX_B_WIDTH}) cannot be smaller than number of vertical partitions ({VERTICAL_PARTITIONS})"
            CLIENT_LOGGER.exception(exception_msg)
            shutdown()
            raise ValueError(exception_msg)

        # Store server(s) results (i.e. Value = Chunk of Matrix A * Chunk of Matrix B at Key = given position)
        self._matrix_products: dict[int, ndarray] = { }

        # Server(s) to send jobs to
        self._server_addresses: list[Address] = self._select_servers()
        CLIENT_LOGGER.info(f"Sending jobs to {self._server_addresses}\n")

        # List to store elements (datatype equal to that of matrices) that have been replaced
        self._replaced_elements: list[int] = [ ]

        # Create and queue partitions of Matrix A and Matrix B and their position, to be sent to selected server(s)
        self._partitions: Queue = self._queue_partitions(matrix_a, matrix_b)

    def _randomly_replace(self, matrix: Matrix, index: int) -> tuple[Matrix, int]:
        """
        Replace random elements in matrix with a variable

        Args:
            matrix (Matrix): Matrix to be redacted
            index (int): Position of replaced element (also number of elements replaced so far)

        Returns:
            tuple[Matrix, int]: Redacted matrix and index of most recently replaced element
        """
        mask = random.default_rng().choice([True, False], size = matrix.shape, shuffle = False)

        for row in range(len(mask)):
            for col in range(len(mask[0])):
                if mask[row][col]:
                    self._replaced_elements.append(matrix[row, col]) # type: ignore
                    matrix[row, col] = X[index]
                    index += 1

        return matrix, index

    def _queue_partitions(self, matrix_a: ndarray, matrix_b: ndarray) -> Queue:
        """
        Create and queue partitions of Matrix A and Matrix B and their position

        Args:
            matrix_a (ndarray): Matrix A
            matrix_b (ndarray): Matrix B

        Returns:
            Queue: Queue of partitions of Matrix A and Matrix B and their position
        """
        start = perf_counter()
        
        # Split matrix horizontally
        sub_matrices = array_split(matrix_a, HORIZONTAL_PARTITIONS, axis = 0)

        # Split submatrices vertically
        matrix_a_partitions, matrix_b_partitions = [m for sub_matrix in sub_matrices for m in  array_split(sub_matrix, VERTICAL_PARTITIONS, axis = 1)], array_split(matrix_b, VERTICAL_PARTITIONS, axis = 0)

        # Declare queue to be populated and returned
        queue = Queue()

        replaced_index = 0
        
        for i in range(len(matrix_a_partitions)):
            # Current subset of Matrix A and Matrix B
            sub_matrix_a, sub_matrix_b = matrix_a_partitions[i], matrix_b_partitions[i % len(matrix_b_partitions)]
            
            # Have client compute some of the partitions (add 1 to account for client)
            if i % (len(self._server_addresses) + 1) == 0:
                self._matrix_products[i] = dot(sub_matrix_a, sub_matrix_b)

            # ...while server(s) compute the rest
            else:
                # Replace random elements in Matrix A with a variable
                redacted_matrix_a, replaced_index = self._randomly_replace(Matrix(sub_matrix_a), replaced_index)
                queue.put((redacted_matrix_a, Matrix(sub_matrix_b), i))

        end = perf_counter()
        CLIENT_LOGGER.info(f"Created partitions and queue in {timing(end, start)} seconds\n")
        
        return queue

    def _combine_results(self, matrix_products: dict[int, ndarray]) -> ndarray:
        """
        Combines submatrices into a single matrix

        Args:
            matrix_products (dict[int, ndarray]): Dictionary to store results (i.e., Value = Chunk of Matrix A * Chunk of Matrix B at Key = given position)

        Returns:
            ndarray: Combined result of given matrices
        """
        start = perf_counter()
        
        # Get all results from the queue, sorted by its position
        results = [value for _, value in sorted(matrix_products.items())]

        # Number of columns, end index, and list for storing combined results
        num_columns, end, combined_results = shape(results[0])[1], 0, []

        # Sum all values in the same row, then add to combined_results
        for i in range(0, len(results), num_columns):
            end += num_columns
            combined_results.append(sum(results[i:end]))

        # Combine all results into a single matrix
        combined_results = concatenate(combined_results)
        
        end = perf_counter()
        CLIENT_LOGGER.info(f"Combined submatrices into a single matrix in {timing(end, start)} seconds\n")
        
        return combined_results

    def get_result(self) -> ndarray:
        """
        Use client and server(s) to multiply matrices, then get result

        Returns:
            ndarray: Product of Matrix A and Matrix B 
        """
        start = perf_counter()
        
        # Send partitioned matrices to randomly selected server(s)
        self._work()

        # Combine [all] results into a single matrix
        result = self._combine_results(self._matrix_products)

        end = perf_counter()
        CLIENT_LOGGER.info(f"Calculated final result in {timing(end, start)} seconds\n")

        # Clean up
        self._cleanup()
        
        return result

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
        start_send = perf_counter()
        
        # Add header to and send data packet to server
        send(server_socket, data)

        end_send = perf_counter()
        CLIENT_LOGGER.info(f"Data sent in {timing(end_send, start_send)} seconds\n")
        start_receive = perf_counter()
        
        # Receive acknowledgment from server
        acknowledgement_data = server_socket.recv(HEADERSIZE)

        # Verify acknowledgment
        acknowledgement_length = int(acknowledgement_data.decode("utf-8").strip())
        acknowledgement_msg = server_socket.recv(acknowledgement_length).decode("utf-8").strip()
        if acknowledgement_msg != ACKNOWLEDGEMENT:
            exception_msg = f"Invalid acknowledgment \"{acknowledgement_msg}\""
            CLIENT_LOGGER.exception(exception_msg)
            shutdown()
            raise ValueError(exception_msg)
                            
        # Receive data from server
        data = receive(server_socket)

        end_receive = perf_counter()
        CLIENT_LOGGER.info(f"Received data in {timing(end_receive, start_receive)} seconds\n")

        return data

    def _read_file_reverse(self, filepath: str = SERVER_INFO_PATH) -> Iterator[str]:
        """
        Read file in reverse

        Args:
            filepath (str, optional): Path of file to read from; defaults to SERVER_INFO_PATH

        Yields:
            Iterator[str]: Line(s) in file at filepath
        """
        with open(filepath, "rb") as file:
            file.seek(0, SEEK_END)
            pointer_location = file.tell()
            buffer = bytearray()

            while pointer_location >= 0:
                file.seek(pointer_location)
                pointer_location -= 1
                new_byte = file.read(1)

                if new_byte == b"\n":
                    yield buffer.decode()[::-1]
                    buffer = bytearray()

                else: buffer.extend(new_byte)

            if len(buffer) > 0: yield buffer.decode()[::-1]

    def _get_available_servers(self, filepath: str = SERVER_INFO_PATH) -> dict[Address, tuple[int, float]]:
        """
        Get all active, listening servers and their CPU, available RAM

        Args:
            filepath (str, optional): Path of file to read from; defaults to SERVER_INFO_PATH

        Raises:
            FileNotFoundError: File containing server information does not exist
            IOError: File containing server information is empty

        Returns:
            dict[Address, tuple[int, float]]: Dictionary of available servers and their CPU, available RAM
        """
        # Ensure file containing server information exists
        if not path.exists(filepath):
            exception_msg = f"File at {filepath} does not exist"
            CLIENT_LOGGER.exception(exception_msg)
            shutdown()
            raise FileNotFoundError(exception_msg)

        # Ensure file containing server information is not empty
        if path.getsize(filepath) == 0:
            exception_msg = f"File at {filepath} is empty"
            CLIENT_LOGGER.exception(exception_msg)
            shutdown()
            raise IOError(exception_msg)

        available_servers = { }
        start = perf_counter()
        
        # Read file containing server addresses, their CPU, and available RAM in reverse (i.e., most recent information first)
        for line in self._read_file_reverse():
            # Skip empty lines or newlines
            if line == "" or line == "\n": continue
            
            # Get IP Address, port, CPU, and available RAM of server
            curr_ip, curr_port, curr_cpu, curr_ram = line.split(" ")[:4]
            curr_address = Address(curr_ip, int(curr_port))

            # Add server address, its CPU, and available RAM to available_servers if not already in it
            if curr_address not in available_servers.keys() and self._is_server_listening(curr_address):
                CLIENT_LOGGER.info(f"Adding info from {line} to available_servers\n")
                available_servers[curr_address] = (int(curr_cpu), float(curr_ram))

        end_read = perf_counter()
        CLIENT_LOGGER.info(f"Read server info file in {timing(end_read, start)} seconds\n")

        return available_servers

    def _is_server_listening(self, server_address: Address) -> bool | None:
        """
        Check if server is listening

        Args:
            server_address (Address): Server address

        Returns:
            bool: True if server is listening, else False
        """
        with socket() as sock:
            sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

            # Server is not listening
            try:
                sock.bind(server_address)
                CLIENT_LOGGER.info(f"{server_address} is not listening\n")
                return False
            
            except error as exception:
                error_num, _ = exception.args
                
                # Server is listening
                if error_num in (EADDRINUSE, EADDRNOTAVAIL):
                    CLIENT_LOGGER.info(f"{server_address} is listening\n")
                    return True

    def _select_servers(self) -> list[Address]:
        """
        Selects a subset of server(s) with the highest compute power to send jobs to
            
        Returns:
            list[Address]: List of server addresses to send jobs to
        """
        # Get available servers and their CPU, available RAM
        available_servers = self._get_available_servers()

        # Select random number between 1 and # of available Servers, inclusive
        num_servers = random.randint(1, len(available_servers) + 1)
        CLIENT_LOGGER.info(f"Generated number of servers to send jobs to = {num_servers}\n")
        
        # Check if all available servers have the same CPU, same available RAM
        same_cpu, same_ram = self._same_cpu_ram(available_servers)

        # TODO Exception handling/catching when length of returned servers != num_servers
        
        if same_cpu:
            if same_ram:
                # Return random sample of available servers since they have same CPU and available RAM
                return sample(list(available_servers.keys()), num_servers)

            # Return top available servers with most available RAM
            else: return sorted(available_servers.keys(), key = lambda x: available_servers[x][1], reverse = True)[:num_servers]
            
        # Return top available servers with highest CPU power
        else: return sorted(available_servers.keys(), key = lambda x: available_servers[x], reverse = True)[:num_servers]

    def _same_cpu_ram(self, servers: dict[Address, tuple[int, float]]) -> tuple[bool, bool]:
        """
        Check whether or not servers have same CPU, same available RAM

        Args:
            servers (dict[Address, tuple[int, float]]): Dictionary of servers and their CPU, available RAM

        Returns:
            tuple[bool, bool]: Whether or not servers have same CPU, same available RAM
        """
        start = perf_counter()
        same_cpu, same_ram, seen_cpu, seen_ram = True, True, set(), set()
        
        for cpu, ram in servers.values():
            if same_cpu:
                if cpu in seen_cpu: same_cpu = False
                else: seen_cpu.add(cpu)

            if same_ram:
                if ram in seen_ram: same_ram = False
                else: seen_ram.add(ram)

            if not same_cpu and not same_ram: break

        end = perf_counter()
        CLIENT_LOGGER.info(f"Checked if servers have same CPU and available RAM in {timing(end, start)} seconds\n")
        
        return same_cpu, same_ram

    def _cleanup(self) -> None:
        """
        Delete instance variables and shutdown logger
        """
        CLIENT_LOGGER.info("Cleaning up...\n")
        del self._matrix_products
        del self._server_addresses
        del self._replaced_elements
        del self._partitions
        shutdown()
        
    @handle_exceptions(CLIENT_LOGGER)
    def _work(self) -> None:
        """
        Send partitioned matrices to server(s), get results,
        then add them to dictionary for combining later
        """
        # Index used to determine where to connect (i.e. cycles through available servers; round robin)
        i = 0

        start_work = perf_counter()

        # While there's still partitions to send to server(s)
        while not self._partitions.empty():
            try:
                with socket() as sock:
                    # Allow reuse of address
                    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

                    # Address of server
                    server_address = self._server_addresses[i % len(self._server_addresses)]

                    # Start timer
                    start = perf_counter()

                    # Connect to server
                    sock.connect(server_address)
                    connection_timer = perf_counter()
                    CLIENT_LOGGER.info(f"Client connected to Server at {server_address} in {timing(connection_timer, start)} seconds\n")

                    # Get partitions to send to server
                    partitions = self._partitions.get(timeout = 0.1)

                    # Receive result from server
                    data = self._handle_server(sock, dumps(partitions))
                    
                    # Unpack data (i.e. position and product of partitions) from server
                    index, result = loads(data)

                    end = perf_counter()
                    CLIENT_LOGGER.info(f"Client connected, sent, received, and unpacked data from Server at {server_address} in {timing(end, start)} seconds\n")

                    # Check if result and index was received (i.e. not None)
                    if result is not None:
                        #print(f"Result Matrix from Server at {server_address} = {result}\n")
                        CLIENT_LOGGER.info(f"Successfully received valid result from Server at {server_address}\n")

                        # Replace variables in result with their actual values
                        actual_matrix = result.subs(X, tuple(self._replaced_elements)).doit()

                        # Cast from SymPy Matrix to NumPy ndarray, then add to dict for concatenation later
                        self._matrix_products[index] = matrix2numpy(actual_matrix, dtype = int)

                    else:
                        CLIENT_LOGGER.error(f"Failed to receive valid result from Server at {server_address}; retrying later...\n")

                        # Put partitions back into queue (since it was previously removed via .get()), to try again later
                        self._partitions.put(partitions)

                    # Increment index
                    i += 1
            
            finally:
                end_work = perf_counter()
                CLIENT_LOGGER.info(f"Client worked for {timing(end_work, start_work)} seconds\n")

    def print_outcome(self, result: ndarray, check: ndarray) -> None:
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
    matrix_b = generate_matrix(LENGTH, MATRIX_B_WIDTH)

    print(f"Matrix A: {matrix_a}\n")
    print(f"Matrix B: {matrix_b}\n")

    # Create Client to multiply matrices
    client = Client(matrix_a, matrix_b)

    # Get result and print it
    answer = client.get_result()
    print(f"Final Result Matrix = {answer}\n")

    # Print outcome (i.e. answer's correctness)
    client.print_outcome(answer, matrix_a @ matrix_b)