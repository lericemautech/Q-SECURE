from collections.abc import Iterator
from socket import socket, SOL_SOCKET, SO_REUSEADDR
from pickle import loads, dumps
from numpy import ndarray, random, array_split, concatenate, dot, shape, array_equal
from queue import Queue
from os import path, SEEK_END
from random import sample
from time import perf_counter
from logging import getLogger, shutdown
from ssl import VERIFY_X509_STRICT, create_default_context, Purpose, TLSVersion
from project.src.ExceptionHandler import handle_exceptions
from project.src.Shared import (Address, ACKNOWLEDGEMENT, HORIZONTAL_PARTITIONS,
                                FILEPATH, SERVER_ADDRESSES, HEADERSIZE, LENGTH,
                                VERTICAL_PARTITIONS, CLIENT_CERT, CLIENT_KEY,
                                CERTIFICATE_AUTHORITY, TLS_LOG,
                                create_logger, receive, send, generate_matrix, timing)

MATRIX_2_WIDTH = 2
CLIENT_LOGGER = getLogger(__name__)

# TODO Implement load balancer for client-servers

class Client():
    def __init__(self, matrix_a: ndarray, matrix_b: ndarray, server_addresses: list[Address] = SERVER_ADDRESSES):
        # Logging
        create_logger("client.log")
        CLIENT_LOGGER.info("Starting Client...\n")

        # Ensure 2nd matrix width is not smaller than number of vertical partitions
        if MATRIX_2_WIDTH < VERTICAL_PARTITIONS:
            exception_msg = f"2nd matrix's width ({MATRIX_2_WIDTH}) cannot be smaller than number of vertical partitions ({VERTICAL_PARTITIONS})"
            CLIENT_LOGGER.exception(exception_msg)
            shutdown()
            raise ValueError(exception_msg)

        # Store server(s) results (i.e. Value = Chunk of Matrix A * Chunk of Matrix B at Key = given position)
        self._matrix_products: dict[int, ndarray] = { }

        # Select random number N between 1 and # of Servers, inclusive
        self._num_servers: int = random.randint(1, len(server_addresses) + 1)
        CLIENT_LOGGER.info(f"Generated number of servers to send jobs to = {self._num_servers}\n")

        # Server(s) to send jobs to        
        self._server_addresses: list[Address] = self._select_servers(server_addresses)
        CLIENT_LOGGER.info(f"Sending jobs to {self._server_addresses}\n")

        # Create context for SSL/TLS connection
        # TODO Catch any SSL/TLS exceptions
        self._context = create_default_context(Purpose.SERVER_AUTH, cafile = CERTIFICATE_AUTHORITY)

        # Load client certificates for SSL/TLS connection
        self._context.load_cert_chain(CLIENT_CERT, CLIENT_KEY)
        
        # Latest version of TLS
        self._context.minimum_version = TLSVersion.TLSv1_3
        self._context.keylog_filename = TLS_LOG
        self._context.verify_flags = VERIFY_X509_STRICT
        self._context.set_ciphers("HIGH:RSA")

        # Create and queue partitions of Matrix A and Matrix B and their position, to be sent to selected server(s)
        self._partitions: Queue = self._queue_partitions(matrix_a, matrix_b)

    def _queue_partitions(self, matrix_a: ndarray, matrix_b: ndarray) -> Queue:
        """
        Create and queue partitions of Matrix A and Matrix B and their position

        Args:
            matrix_a (ndarray): Matrix A
            matrix_b (ndarray): Matrix B

        Returns:
            Queue: Queue of partitions of Matrix A and Matrix B and their position
        """
        # Start timer
        start = perf_counter()
        
        # Split matrix horizontally
        sub_matrices = array_split(matrix_a, HORIZONTAL_PARTITIONS, axis = 0)

        # Split submatrices vertically
        matrix_a_partitions, matrix_b_partitions = [m for sub_matrix in sub_matrices for m in  array_split(sub_matrix, VERTICAL_PARTITIONS, axis = 1)], array_split(matrix_b, VERTICAL_PARTITIONS, axis = 0)

        # Declare queue to be populated and returned
        queue = Queue()
        
        for i in range(len(matrix_a_partitions)):
            # Have client compute some of the partitions; add 1 to num_servers to account for client
            if i % (self._num_servers + 1) == 0:
                self._matrix_products[i] = dot(matrix_a_partitions[i], matrix_b_partitions[i % len(matrix_b_partitions)])

            # ...while server(s) compute the rest
            else:
                queue.put((matrix_a_partitions[i], matrix_b_partitions[i % len(matrix_b_partitions)], i))

        # End timer
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
        # Start timer
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
        
        # End timer
        end = perf_counter()
        CLIENT_LOGGER.info(f"Combined submatrices into a single matrix in {timing(end, start)} seconds\n")
        
        return combined_results

    def get_result(self) -> ndarray:
        """
        Use client and server to multiply matrices, then get result

        Returns:
            ndarray: Product of Matrix A and Matrix B 
        """
        # Start timer
        start = perf_counter()
        
        # Send partitioned matrices to randomly selected server(s)
        self._work()

        # Combine [all] results into a single matrix
        result = self._combine_results(self._matrix_products)

        # End timer
        end = perf_counter()
        CLIENT_LOGGER.info(f"Calculated final result in {timing(end, start)} seconds\n")

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
        ack_data = server_socket.recv(HEADERSIZE)

        # Verify acknowledgment
        ack_msg_length = int(ack_data.decode("utf-8").strip())
        ack_msg = server_socket.recv(ack_msg_length).decode("utf-8").strip()
        if ack_msg != ACKNOWLEDGEMENT:
            exception_msg = f"Invalid acknowledgment \"{ack_msg}\""
            CLIENT_LOGGER.exception(exception_msg)
            shutdown()
            raise ValueError(exception_msg)
                            
        # Receive data from server
        data = receive(server_socket)

        end_receive = perf_counter()
        CLIENT_LOGGER.info(f"Received data in {timing(end_receive, start_receive)} seconds\n")

        return data

    def _read_file_reverse(self, filepath: str = FILEPATH) -> Iterator[str]:
        """
        Read file in reverse

        Args:
            filepath (str, optional): Path of file to read from; defaults to FILEPATH

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

    def _select_servers(self, server_addresses: list[Address]) -> list[Address]:
        """
        Selects a subset of server(s) with the highest compute power to send jobs to

        Args:
            server_addresses (list[Address]): List of server addresses

        Raises:
            ValueError: Invalid number of servers
            FileNotFoundError: File containing server information does not exist
            IOError: File containing server information is empty
            
        Returns:
            list[Address]: List of server addresses to send jobs to
        """
        if self._num_servers > len(server_addresses) or self._num_servers < 1:
            exception_msg = f"{self._num_servers} is an invalid number of servers"
            CLIENT_LOGGER.exception(exception_msg)
            shutdown()
            raise ValueError(exception_msg)

        if not path.exists(FILEPATH):
            exception_msg = f"File at {FILEPATH} does not exist"
            CLIENT_LOGGER.exception(exception_msg)
            shutdown()
            raise FileNotFoundError(exception_msg)

        if path.getsize(FILEPATH) == 0:
            exception_msg = f"File at {FILEPATH} is empty"
            CLIENT_LOGGER.exception(exception_msg)
            shutdown()
            raise IOError(exception_msg)

        valid_servers = { }
        start = perf_counter()
        
        # Read file containing server addresses, their CPU, and available RAM in reverse (i.e., most recent information first)
        for line in self._read_file_reverse():
            if line == "" or line == "\n": continue
            # Get IP Address, port, CPU, and available RAM of server
            curr_ip, curr_port, curr_cpu, curr_ram = line.split(" ")[:4]
            curr_address = Address(curr_ip, int(curr_port))

            # Add server address, its CPU, and available RAM to valid_servers if not already in it
            if curr_address not in valid_servers.keys() and self._is_server_listening(curr_address):
                CLIENT_LOGGER.info(f"Adding info from {line} to valid_servers\n")
                valid_servers[curr_address] = (int(curr_cpu), float(curr_ram))

        end_read = perf_counter()
        CLIENT_LOGGER.info(f"Read file in {timing(end_read, start)} seconds\n")
        
        # Check if all valid servers have the same CPU, same available RAM
        same_cpu, same_ram = self._same_cpu_ram(valid_servers)
        
        if same_cpu:
            if same_ram:
                # Return random sample of valid servers since they have same CPU and available RAM
                return sample(list(valid_servers.keys()), self._num_servers)

            # Return top valid servers with most available RAM
            else: return sorted(valid_servers.keys(), key = lambda x: valid_servers[x][1], reverse = True)[:self._num_servers]
            
        # Return top valid servers with highest CPU power
        else: return sorted(valid_servers.keys(), key = lambda x: valid_servers[x], reverse = True)[:self._num_servers]

    # TODO Create data structure for dict[Address, tuple[int, float]]
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

    def _is_server_listening(self, address: Address) -> bool:
        """
        Check if server is listening

        Args:
            address (Address): Server address

        Returns:
            bool: True if server is listening, else False
        """
        with socket() as sock:
            sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

            try:
                sock.connect_ex(address)
                CLIENT_LOGGER.info(f"Server at {address} is listening\n")
                return True

            except:
                CLIENT_LOGGER.error(f"Server at {address} is not listening\n")
                return False
        
    @handle_exceptions(CLIENT_LOGGER)
    def _work(self) -> None:
        """
        Send partitioned matrices to server(s), get results,
        then add them to dictionary for combining later
        """
        # Index used to determine where to connect (i.e. cycles through available servers; round robin)
        i = 0

        # Start method's timer
        start_work = perf_counter()

        # While there's still partitions to send to server(s)
        while not self._partitions.empty():
            try:
                #with self._context.wrap_socket(socket(AF_INET, SOCK_STREAM), server_hostname = SERVER_SNI_HOSTNAME) as sock:
                with socket() as sock:
                    #sock = self._context.wrap_socket(sock, server_hostname = SERVER_SNI_HOSTNAME)
                    # Allow reuse of address
                    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

                    # Address of server
                    server_address = self._server_addresses[i % len(self._server_addresses)]

                    sock = self._context.wrap_socket(sock, server_hostname = server_address.ip)

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

                    # End timer
                    end = perf_counter()

                    CLIENT_LOGGER.info(f"Client connected, sent, received, and unpacked data from Server at {server_address} in {timing(end, start)} seconds\n")

                    # Check if result and index was received (i.e. not None)
                    if result is not None:
                        #print(f"Result Matrix from Server at {server_address} = {result}\n")
                        CLIENT_LOGGER.info(f"Successfully received valid result from Server at {server_address}\n")

                        # Add result to dict, to be combined into final result later
                        self._matrix_products[index] = result

                    else:
                        CLIENT_LOGGER.error(f"Failed to receive valid result from Server at {server_address}; retrying later...\n")

                        # Put partitions back into queue (since it was previously removed via .get()), to try again later
                        self._partitions.put(partitions)

                    # Increment index
                    i += 1
            
            finally:
                # End method's timer
                end_work = perf_counter()

                # Log Client's work time
                CLIENT_LOGGER.info(f"Client worked for {timing(end_work, start_work)} seconds\n")
                                
                # Stop logging
                shutdown()

    def print_outcome(self, result: ndarray, check: ndarray) -> None:
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
    # Generate example matrices for testing
    matrix_a = generate_matrix(LENGTH, LENGTH)
    matrix_b = generate_matrix(LENGTH, MATRIX_2_WIDTH)

    print(f"Matrix A: {matrix_a}\n")
    print(f"Matrix B: {matrix_b}\n")

    # Create Client to multiply matrices
    client = Client(matrix_a, matrix_b)

    # Get result
    answer = client.get_result()
    print(f"Final Result Matrix = {answer}\n")

    # Print outcome (i.e. answer's correctness)
    client.print_outcome(answer, matrix_a @ matrix_b)