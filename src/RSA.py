from Crypto.Util.number import getPrime
from Crypto.IO.PEM import encode, decode
from math import gcd
from numpy import frombuffer, reshape, ndarray, random

N_BITS = 8 # Must be larger than 1

# TODO Add support for larger numbers/matrices
# TODO Add detailed math explanation/equation for RSA methods + comments

class RSA():
    def __init__(self, num_bits: int = N_BITS):
        self._num_bits: int = num_bits
        self._n, self._e, self._d = self._generate_keys(num_bits)

    def encrypt(self, data: bytes) -> list[int]:
        """
        Encrypt given data using RSA algorithm

        Encryption = (data)^e mod n

        Args:
            data (bytes): Data to encrypt

        Returns:
            list[int]: Encrypted data
        """
        return [pow(c, self._e, self._n) for c in data]

    def decrypt(self, data: list[int]) -> bytes:
        """
        Decrypt given data using RSA algorithm

        Decryption = (data)^d mod n

        Args:
            data (list[int]): Data to decrypt

        Returns:
            bytes: Decrypted data
        """
        return b"".join([pow(c, self._d, self._n).to_bytes() for c in data])

    def _generate_keys(self, num_bits: int = N_BITS) -> tuple[int, int, int]:
        """
        Generate public (e, n) and private (d, n) keys using RSA algorithm

        1. Select 2 random N-bit prime numbers p, q
        2. Calculate n = p * q
        3. Calculate totient = (p - 1) * (q - 1)
        4. Select e such that 1 < e < totient and gcd(totient, e) = 1
        5. d = e^-1 mod totient

        Args:
            num_bits (int, optional): Number of bits; defaults to N_BITS

        Returns:
            tuple[int, int, int]: Values (n, e, d) used for public and private keys
        """
        # Select 2 random N-bit prime numbers
        p, q = self._generate_primes(num_bits)

        # Calculate n and totient
        n, totient = (p * q), (p - 1) * (q - 1)

        # Initialize e
        e = 2

        # Select e such that 1 < e < totient...
        for e in range(2, totient):
            #  ...and gcd(totient, e) = 1
            if gcd(e, totient) == 1:
                break

        return (n, e, pow(e, -1, totient))

    def _write_keys(self, filename: str, key) -> None:
        export_key = encode(key, "PUBLIC KEY")
        with open(filename, "w") as file:
            print(f"{decode(export_key)}", file = file)

    def _generate_primes(self, num_bits: int = N_BITS) -> tuple[int, int]:
        """
        Return a random N-bit prime number

        Args:
            num_bits (int, optional): Number of bits; defaults to N_BITS

        Raises:
            ValueError: Number of bits must be an integer larger than 1

        Returns:
            tuple[int, int]: 2 randomly generated N-bit prime numbers
        """
        # Ensure num_bits is an integer larger than 1
        if num_bits < 2:
            raise ValueError("Number of bits must be larger than 1")

        # Select 2 random N-bit prime numbers
        p = getPrime(num_bits)
        q = getPrime(num_bits)

        # Ensure p != q
        while p == q:
            # If they're equal, generate 2 new random N-bit prime numbers
            p = getPrime(num_bits)
            q = getPrime(num_bits)

            # Check if they're equal again, and repeat if necessary
            if p != q:
                return p, q

        return p, q

    def _matrix_to_bytes(self, matrix: ndarray) -> bytes:
        """
        Convert matrix to bytes for encryption

        Args:
            matrix (ndarray): Matrix to convert to bytes

        Returns:
            bytes: Matrix in bytes form
        """
        return matrix.tobytes()

    def decrypt_matrix(self, data, shape) -> ndarray:
        """
        Decrypt matrix

        Args:
            data (_type_): Matrix to decrypt
            shape (_type_): Matrix shape

        Returns:
            ndarray: Decrypted matrix
        """
        return reshape(frombuffer(cipher.decrypt(data), dtype = int), newshape = shape)

if __name__ == "__main__":
    cipher = RSA()
    
    msg = 5
    print("msg =", msg)
    encrypted = cipher.encrypt(msg.to_bytes())
    print("encrypted =", encrypted)
    decrypted = cipher.decrypt(encrypted)
    print("decrypted =", int.from_bytes(decrypted))

    matrix = random.randint(0, 128, size = (4, 4), dtype = int)
    print("\noriginal matrix =", matrix)
    e = cipher._matrix_to_bytes(matrix)
    encrypted = cipher.encrypt(e)
    print("\nencrypted =", encrypted)
    decrypted = cipher.decrypt_matrix(encrypted, matrix.shape)
    print("\ndecrypted =", decrypted)