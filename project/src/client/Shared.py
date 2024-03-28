from numpy import ndarray, random, concatenate, array_equal
from time import perf_counter
from random import sample
from logging import Logger
from socket import socket, error, SOL_SOCKET, SO_REUSEADDR
from collections.abc import Iterator
from errno import EADDRINUSE, EADDRNOTAVAIL
from os import path, SEEK_END
from project.src.Shared import (timing, send, receive, cleanup, Address, ACKNOWLEDGEMENT, HORIZONTAL_PARTITIONS,
                                VERTICAL_PARTITIONS, HEADERSIZE, SERVER_INFO_PATH)

MATRIX_B_WIDTH = 4
"""Matrix B's width"""

def validate_inputs(length: int, matrix_b_width: int, logger: Logger) -> None:
    """
    Ensure matrix dimensions are valid

    Args:
        length (int): Matrix A and Matrix B's length
        matrix_b_width (int): Matrix B's width
        logger (Logger): Logger

    Raises:
        ValueError: Invalid matrix shape
    """
    # Ensure Matrix length is not smaller than number of horizontal and/or vertical partitions
    if length < (HORIZONTAL_PARTITIONS or VERTICAL_PARTITIONS):
        exception_msg = f"Matrix length ({length}) cannot be smaller than number of horizontal ({HORIZONTAL_PARTITIONS}) and/or vertical ({VERTICAL_PARTITIONS}) partitions"
        logger.exception(exception_msg)
        cleanup(logger)
        raise ValueError(exception_msg)

    # Ensure Matrix B's width is not smaller than number of vertical partitions
    elif matrix_b_width < VERTICAL_PARTITIONS:
        exception_msg = f"Matrix B's width ({matrix_b_width}) cannot be smaller than number of vertical ({VERTICAL_PARTITIONS}) partitions"
        logger.exception(exception_msg)
        cleanup(logger)
        raise ValueError(exception_msg)

def combine_results(matrix_products: dict[int, ndarray], logger: Logger) -> ndarray:
    """
    Combines submatrices into a single matrix

    Args:
        matrix_products (dict[int, ndarray]): Dictionary to store results (i.e., Value = Chunk of Matrix A * Chunk of Matrix B at Key = given position)
        logger (Logger): Logger
        
    Returns:
        ndarray: Combined result of given matrices
    """
    start = perf_counter()
    
    # Get all results from the queue, sorted by its position
    results = [value for _, value in sorted(matrix_products.items())]

    # End index and list for storing combined results
    end, combined_results = 0, []

    # Sum all values in the same row, then add to combined_results
    for i in range(0, len(results), VERTICAL_PARTITIONS):
        end += VERTICAL_PARTITIONS
        combined_results.append(sum(results[i:end]))

    # Combine all results into a single matrix
    combined_results = concatenate(combined_results)
    
    end = perf_counter()
    logger.info(f"Combined submatrices into a single matrix in {timing(end, start)} seconds\n")
    
    return combined_results

def handle_server(server_socket: socket, data: bytes, logger: Logger) -> bytes:
    """
    Exchange data with server

    Args:
        server_socket (socket): Server socket
        data (bytes): Data to be sent
        logger (Logger): Logger

    Raises:
        ValueError: Invalid acknowledgment

    Returns:
        bytes: Data received from server
    """
    start_send = perf_counter()
    
    # Add header to and send data packet to server
    send(server_socket, data)

    end_send = perf_counter()
    logger.info(f"Data sent in {timing(end_send, start_send)} seconds\n")
    start_receive = perf_counter()
    
    # Receive acknowledgment from server
    acknowledgement_data = server_socket.recv(HEADERSIZE)

    # Verify acknowledgment
    acknowledgement_length = int(acknowledgement_data.decode("utf-8").strip())
    acknowledgement_msg = server_socket.recv(acknowledgement_length).decode("utf-8").strip()
    if acknowledgement_msg != ACKNOWLEDGEMENT:
        exception_msg = f"Invalid acknowledgment \"{acknowledgement_msg}\""
        logger.exception(exception_msg)
        raise ValueError(exception_msg)
                        
    # Receive data from server
    data = receive(server_socket)

    end_receive = perf_counter()
    logger.info(f"Received data in {timing(end_receive, start_receive)} seconds\n")

    return data

def read_file_reverse(filepath: str = SERVER_INFO_PATH) -> Iterator[str]:
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

def get_available_servers(logger: Logger, filepath: str = SERVER_INFO_PATH) -> dict[Address, tuple[int, float]]:
    """
    Get all active, listening servers and their CPU, available RAM

    Args:
        logger (Logger): Logger
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
        logger.exception(exception_msg)
        raise FileNotFoundError(exception_msg)

    # Ensure file containing server information is not empty
    if path.getsize(filepath) == 0:
        exception_msg = f"File at {filepath} is empty"
        logger.exception(exception_msg)
        raise IOError(exception_msg)

    available_servers = { }
    start = perf_counter()
    
    # Read file containing server addresses, their CPU, and available RAM in reverse (i.e., most recent information first)
    for line in read_file_reverse():
        # Skip empty lines or newlines
        if line == "" or line == "\n": continue
        
        # Get IP Address, port, CPU, and available RAM of server
        curr_ip, curr_port, curr_cpu, curr_ram = line.split(" ")[:4]
        curr_address = Address(curr_ip, int(curr_port))

        # Add server address, its CPU, and available RAM to available_servers if not already in it
        if curr_address not in available_servers.keys() and is_server_listening(curr_address, logger):
            logger.info(f"Adding info from {line} to available_servers\n")
            available_servers[curr_address] = (int(curr_cpu), float(curr_ram))

    end_read = perf_counter()
    logger.info(f"Read server info file in {timing(end_read, start)} seconds\n")

    return available_servers

def is_server_listening(server_address: Address, logger: Logger) -> bool | None:
    """
    Check if server is listening

    Args:
        server_address (Address): Server address
        logger (Logger): Logger

    Returns:
        bool: True if server is listening, else False
    """
    with socket() as sock:
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        # Server is not listening
        try:
            sock.bind(server_address)
            logger.info(f"{server_address} is not listening\n")
            return False
        
        except error as exception:
            error_num, _ = exception.args
            
            # Server is listening
            if error_num in (EADDRINUSE, EADDRNOTAVAIL):
                logger.info(f"{server_address} is listening\n")
                return True

def select_servers(logger: Logger) -> list[Address]:
    """
    Selects a subset of server(s) with the highest compute power to send jobs to

    Args:
        logger (Logger): Logger
        
    Returns:
        list[Address]: List of server addresses to send jobs to
    """
    # Get available servers and their CPU, available RAM
    available_servers = get_available_servers(logger)

    # Select random number between 1 and # of available Servers, inclusive
    num_servers = random.randint(1, len(available_servers) + 1)
    logger.info(f"Generated number of servers to send jobs to = {num_servers}\n")
    
    # Check if all available servers have the same CPU, same available RAM
    same_cpu, same_ram = same_cpu_ram(available_servers, logger)

    # TODO Exception handling/catching when length of returned servers != num_servers
    
    if same_cpu:
        if same_ram:
            # Return random sample of available servers since they have same CPU and available RAM
            return sample(list(available_servers.keys()), num_servers)

        # Return top available servers with most available RAM
        else: return sorted(available_servers.keys(), key = lambda x: available_servers[x][1], reverse = True)[:num_servers]
        
    # Return top available servers with highest CPU power
    else: return sorted(available_servers.keys(), key = lambda x: available_servers[x], reverse = True)[:num_servers]

def same_cpu_ram(servers: dict[Address, tuple[int, float]], logger: Logger) -> tuple[bool, bool]:
    """
    Check whether or not servers have same CPU, same available RAM

    Args:
        servers (dict[Address, tuple[int, float]]): Dictionary of servers and their CPU, available RAM
        logger (Logger): Logger

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
    logger.info(f"Checked if servers have same CPU and available RAM in {timing(end, start)} seconds\n")
    
    return same_cpu, same_ram

def get_result(self, logger: Logger) -> ndarray:
    """
    Use client and server(s) to multiply matrices, then get result

    Args:
        logger (Logger): Logger

    Returns:
        ndarray: Product of Matrix A and Matrix B 
    """
    start = perf_counter()
    
    # Send partitioned matrices to randomly selected server(s)
    self._work()

    # Combine [all] results into a single matrix
    result = combine_results(self._matrix_products, logger)

    end = perf_counter()
    logger.info(f"Calculated final result in {timing(end, start)} seconds\n")
    
    return result

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