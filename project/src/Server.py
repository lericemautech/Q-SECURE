from socket import socket, error, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from pickle import loads, dumps
from numpy import ndarray, dot, empty, sum, concatenate
from typing import NamedTuple
from os import cpu_count, path, rename
from platform import platform
from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import getLogger, shutdown
from logging.config import fileConfig
from project.src.Shared import Address, receive, send, partition, DIRECTORY_PATH, FILENAME, VERTICAL_PARTITIONS, LOG_CONF_PATH

SERVER_LOGFILE = "server.log"
SERVER_LOGGER = getLogger(__name__)

class Matrix(NamedTuple):
    matrix: ndarray
    index: int

class Server():
    def __init__(self, address: Address, directory_path: str = DIRECTORY_PATH):
        # Logging
        fileConfig(LOG_CONF_PATH, defaults = { "logfilename" : SERVER_LOGFILE}, disable_existing_loggers = False)

        # Server's IP Address and port
        self._server_address = address

        # Check if directory_path exists
        if not path.exists(directory_path):
            exception_msg = f"{directory_path} does not exist"
            SERVER_LOGGER.exception(exception_msg)
            shutdown()
            raise IOError(exception_msg)

        # Check if directory_path is actually a directory
        if not path.isdir(directory_path):
            exception_msg = f"{directory_path} is not a directory"
            SERVER_LOGGER.exception(exception_msg)
            shutdown()
            raise NotADirectoryError(exception_msg)

        # Write Server's IP Address, port, number of cores, and OS to file in directory_path
        self._document_info(directory_path)
    
    def _document_info(self, directory_path: str = DIRECTORY_PATH, filename: str = FILENAME, remove_duplicates: bool = False) -> None:
        """
        Document server's IP Address, port, number of cores, and OS to FILENAME at directory_path

        Args:
            directory_path (str, optional): Path of the directory to write the file to; defaults to DIRECTORY_PATH
            filename (str, optional): Name of the file to write to; defaults to FILENAME
            remove_duplicates (bool, optional): Whether to remove entries with the same IP address
            and port as current Server; defaults to False
        """
        # Get current Server's IP Address and port
        ip, port = self._server_address.ip, self._server_address.port

        # Path of file to write to
        filepath = path.join(directory_path, filename)

        # Removes entries with the same IP Address and port as current Server
        if remove_duplicates and path.isfile(filepath):
            if path.getsize(filepath) > 0:
                # Path of temporary file to write to
                temp_filepath = path.join(directory_path, f"temp_{filename}")

                # Read from original filepath and write to temporary filepath
                with open(filepath, "r") as in_file, open(temp_filepath, "w+") as out_file:
                    for line in in_file:
                        # Split line into list (i.e. [IP Address, port, number of cores, OS])
                        server_info = line.split(" ")

                        # Make sure line is valid (i.e. has at least IP Address and port)
                        if len(server_info) < 2:
                            SERVER_LOGGER.error(f"Invalid line: {line}\n")
                            continue
                        
                        # Get IP Address and port at current line
                        curr_ip, curr_port = server_info[:2]

                        # Write line to temp_server_info.txt if IP Address and port are not the same as current Server
                        if curr_ip != ip and curr_port != port:
                            out_file.write(line)

                # Rename temporary filepath to original filepath
                rename(temp_filepath, filepath)

        # Append (i.e. write at end) Server's IP Address, port, number of cores, and OS to file
        with open(filepath, "a") as file:
            file.write(f"{ip} {port} {cpu_count()} {platform(terse = True)}\n")

    def _multiply(self, matrix_a: ndarray, matrix_b: ndarray, index: int) -> Matrix:
        """
        Multiply 2 matrices using multithreading

        Args:
            matrix_a (ndarray): Matrix A
            matrix_b (ndarray): Matrix B
            index (int): Matrix position

        Returns:
            Matrix: Multiple of Matrix A and Matrix B, its position
        """
        #return Matrix(dot(matrix_a, matrix_b), index)

        # TODO Threading ONLY for very large matrices (i.e. LENGTH > 10000?)
        matrix_a_partitions, matrix_b_partitions = partition(matrix_a, matrix_b)
        threads, results, num = [ ], empty(len(matrix_a_partitions), dtype = ndarray), 0

        # Use threads to multiply partitioned matrices
        with ThreadPoolExecutor() as executor:
            for i in range(len(matrix_a_partitions)):
                threads.append(executor.submit(lambda m1, m2, i: Matrix(dot(m1, m2), i), matrix_a_partitions[i], matrix_b_partitions[i % VERTICAL_PARTITIONS], num))

                # Keep track of position
                num += 1

            # Get completed thread's result and store in proper order
            for thread in as_completed(threads):
                result, num = thread.result()
                results[num] = result

        # TODO Rewrite this into method in Shared.py
        # Number of columns, end index, and list for storing combined results
        end, combined_results =  0, []

        # Sum all values in the same row, then add to combined_results
        for i in range(0, len(results), VERTICAL_PARTITIONS):
            end += VERTICAL_PARTITIONS
            combined_results.append(sum(results[i:end]))

        # Combine all results into a single matrix and return
        return Matrix(concatenate(combined_results), index)
        
    def _send_client(self, client_socket: socket, data: bytes) -> None:
        """
        Send data to client

        Args:
            client_socket (socket): Client socket
            data (bytes): Message packet (i.e. data) to send to client
        """
        # Add header to and send acknowledgment packet
        send(client_socket, "ACK".encode("utf-8"))
        
        # Add header to and send message packet back to client
        send(client_socket, data)

    def _handle_client(self, client_socket: socket) -> None:
        """
        Get partitions of Matrix A and Matrix B from client, multiply them, then send result back to client

        Args:
            client_socket (socket): Client socket
        """
        # Receive data from client
        data = receive(client_socket)

        # Unpack data (i.e. partitions of Matrix A and Matrix B and their position)
        matrix_a_partition, matrix_b_partition, index = loads(data)
        received_msg = f"Received [{index}]: {matrix_a_partition} and {matrix_b_partition}"
        #SERVER_LOGGER.info(received_msg)
        print(received_msg)

        # Multiply partitions of Matrix A and Matrix B, while keeping track of their position
        result = self._multiply(matrix_a_partition, matrix_b_partition, index)
    
        # Convert result to bytes, then send back to client
        self._send_client(client_socket, dumps(result))
        sent_msg = f"Sent: {result}"
        #SERVER_LOGGER.info(sent_msg)
        print(f"\n{sent_msg}\n")

    def start_server(self) -> None:
        """
        Start server and listen for connections

        Raises:
            BrokenPipeError: Unable to write to shutdown socket
            ConnectionRefusedError: Connection refused
            ConnectionAbortedError: Connection aborted
            ConnectionResetError: Connection reset
            ConnectionError: Connection lost
            TimeoutError: Connection timed out
            KeyboardInterrupt: Server disconnected due to keyboard (i.e. CTRL + C)
        """
        try:
            with socket(AF_INET, SOCK_STREAM) as server_socket:
                # Allow reuse of address
                server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

                # Bind socket to server's address
                server_socket.bind(self._server_address)

                # Listen for connection(s)
                server_socket.listen()
                listen_msg = f"Server at {self._server_address} listening for connection(s)...\n"
                SERVER_LOGGER.info(listen_msg)
                print(listen_msg)

                while True:
                    # Accept connection from client
                    client_socket, client_address = server_socket.accept()
                    accepted_connection_msg = f"Accepted connection from {client_address}\n"
                    SERVER_LOGGER.info(accepted_connection_msg)
                    print(accepted_connection_msg)

                    # Handle client (i.e. get position and partitions of Matrix A and Matrix B,
                    # multiply them, then send result and its position back to client)
                    self._handle_client(client_socket)

        except BrokenPipeError as exception:
            exception_msg = "(Server._start_server) Unable to write to shutdown socket"
            SERVER_LOGGER.exception(exception_msg)
            shutdown()
            raise BrokenPipeError(exception_msg) from exception

        except ConnectionRefusedError as exception:
            exception_msg = f"(Server._start_server) Connection refused"
            SERVER_LOGGER.exception(exception_msg)
            shutdown()
            raise ConnectionRefusedError(exception_msg) from exception
        
        except ConnectionAbortedError as exception:
            exception_msg = "(Server._start_server) Connection aborted"
            SERVER_LOGGER.exception(exception_msg)
            shutdown()
            raise ConnectionAbortedError(exception_msg) from exception

        except ConnectionResetError as exception:
            exception_msg = "(Server._start_server) Connection reset"
            SERVER_LOGGER.exception(exception_msg)
            shutdown()
            raise ConnectionResetError(exception_msg) from exception
    
        except ConnectionError as exception:
            exception_msg = f"(Server._start_server) Connection lost"
            SERVER_LOGGER.exception(exception_msg)
            shutdown()
            raise ConnectionError(exception_msg) from exception

        except TimeoutError as exception:
            exception_msg = "(Server._start_server) Connection timed out"
            SERVER_LOGGER.exception(exception_msg)
            shutdown()
            raise TimeoutError(exception_msg) from exception

        except KeyboardInterrupt:
            msg = f"Server at {self._server_address} disconnected"
            SERVER_LOGGER.info(msg)
            print(f"\n{msg}")
            shutdown()
            exit(0)

        except error as exception:
            exception_msg = f"(Server._start_server) {exception}"
            SERVER_LOGGER.exception(exception_msg)
            print(f"EXCEPTION: {exception_msg}")
            shutdown()
            exit(1)