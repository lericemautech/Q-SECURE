from socket import socket, SOL_SOCKET, SO_REUSEADDR
from pickle import loads, dumps
from numpy import ndarray, random, array_split, dot
from queue import Queue
from time import perf_counter
from logging import getLogger
from sympy import IndexedBase, Matrix, matrix2numpy
from project.src.ExceptionHandler import handle_exceptions
from project.src.client.Shared import get_result, handle_server, select_servers, print_outcome, validate_inputs, MATRIX_B_WIDTH
from project.src.Shared import (Address, create_logger, generate_matrix, timing,
                                HORIZONTAL_PARTITIONS, LENGTH, VERTICAL_PARTITIONS)

X = IndexedBase("x")
"""Base of subscriptable variable used to replace elements in matrix"""

CLIENT_LOGGER = getLogger(__name__)
"""Client logger"""

# TODO Threading in Substitution Client where there's 1 thread for each Server connection

class SubstitutionClient():
    def __init__(self, matrix_a: ndarray, matrix_b: ndarray, length: int = LENGTH, matrix_b_width: int = MATRIX_B_WIDTH):
        create_logger("client.log")
        CLIENT_LOGGER.info("Starting Substitution Client...\n")

        # Ensure matrix dimensions are valid
        validate_inputs(length, matrix_b_width, CLIENT_LOGGER)

        # Store server(s) results (i.e. Value = Chunk of Matrix A * Chunk of Matrix B at Key = given position)
        self._matrix_products: dict[int, ndarray] = { }

        # Server(s) to send jobs to
        self._server_addresses: list[Address] = select_servers(CLIENT_LOGGER)
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
        
        # Split Matrix A horizontally
        sub_matrices = array_split(matrix_a, HORIZONTAL_PARTITIONS, axis = 0)

        # Split Matrix A vertically and split Matrix B horizontally using VERTICAL_PARTITIONS (i.e., Matrix A's vertical partitions width should equal Matrix B's horizontal partitions length)
        matrix_a_partitions, matrix_b_partitions = [m for sub_matrix in sub_matrices for m in  array_split(sub_matrix, VERTICAL_PARTITIONS, axis = 1)], array_split(matrix_b, VERTICAL_PARTITIONS, axis = 0)
        
        # Declare queue to be populated and returned
        queue = Queue()

        replaced_index = 0
        
        for i in range(len(matrix_a_partitions)):
            # Current subset of Matrix A and Matrix B
            sub_matrix_a, sub_matrix_b = matrix_a_partitions[i], matrix_b_partitions[i % VERTICAL_PARTITIONS]

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

    def answer(self) -> ndarray:
        """
        Use client and server(s) to multiply matrices, then get result

        Returns:
            ndarray: Product of Matrix A and Matrix B 
        """
        return get_result(self, CLIENT_LOGGER)
        
    @handle_exceptions(CLIENT_LOGGER)
    # TODO Create separate client instances for each server
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
                    CLIENT_LOGGER.info(f"Substitution Client connected to Server at {server_address} in {timing(connection_timer, start)} seconds\n")

                    # Get partitions to send to server
                    partitions = self._partitions.get(timeout = 0.1)
                    print(f"Sending to server: {partitions}\n")

                    # Receive result from server
                    data = handle_server(sock, dumps(partitions), CLIENT_LOGGER)
                    
                    # Unpack data (i.e. position and product of partitions) from server
                    index, result = loads(data)

                    end = perf_counter()
                    CLIENT_LOGGER.info(f"Substitution Client connected, sent, received, and unpacked data from Server at {server_address} in {timing(end, start)} seconds\n")

                    # Check if result and index was received (i.e. not None)
                    if result is not None:
                        CLIENT_LOGGER.info(f"Successfully received valid result from Server at {server_address}\n")
                        #print(f"Redacted result Matrix from Server at {server_address} = {result}\n")

                        # Start timer
                        start = perf_counter()

                        # Replace variables in result with their actual values
                        actual_matrix = result.subs(X, tuple(self._replaced_elements)).doit()

                        # End timer
                        end = perf_counter()
                        CLIENT_LOGGER.info(f"Replaced variables in result with their actual values in {timing(end, start)} seconds\n")

                        # Start timer
                        start = perf_counter()
                        
                        # Cast from SymPy Matrix to NumPy ndarray, then add to dict for concatenation later
                        self._matrix_products[index] = matrix2numpy(actual_matrix, dtype = int)

                        # End timer
                        end = perf_counter()
                        CLIENT_LOGGER.info(f"Converted SymPy Matrix to NumPy ndarray in {timing(end, start)} seconds\n")

                    else:
                        CLIENT_LOGGER.error(f"Failed to receive valid result from Server at {server_address}; retrying later...\n")

                        # Put partitions back into queue (since it was previously removed via .get()), to try again later
                        self._partitions.put(partitions)

                    # Increment index
                    i += 1
            
            finally:
                end_work = perf_counter()
                CLIENT_LOGGER.info(f"Substitution Client worked for {timing(end_work, start_work)} seconds\n")

if __name__ == "__main__":
    # Generate example matrices for testing
    matrix_a = generate_matrix(LENGTH, LENGTH)
    matrix_b = generate_matrix(LENGTH, MATRIX_B_WIDTH)

    print(f"Matrix A: {matrix_a}\n")
    print(f"Matrix B: {matrix_b}\n")
    start = perf_counter()

    # Create Substitution Client to multiply matrices
    encrypted_client = SubstitutionClient(matrix_a, matrix_b)

    # Get result
    answer = encrypted_client.answer()

    end = perf_counter()
    print(f"Final Result Matrix = {answer}\n")
    print(f"Substitution Client ran for {end - start} seconds\n")

    # Print outcome (i.e. answer's correctness)
    print_outcome(answer, matrix_a @ matrix_b)