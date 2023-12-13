from Crypto.Util.number import getPrime
from math import gcd

N_BITS = 8 # Must be larger than 1

class RSA():
    def __init__(self, num_bits: int = N_BITS):
        self._n, self._e, self._d = self._generate_keys(num_bits)

    def encrypt(self, plain_text: str) -> list[int]:
        """
        Encrypt given plain text

        Args:
            plain_text (str): Message to encrypt

        Returns:
            list[int]: Encrypted message
        """
        return [pow(ord(c), self._e, self._n) for c in plain_text]

    def decrypt(self, cipher_text: list[int]) -> str:
        """
        Decrypt given cipher text

        Args:
            cipher_text (list[int]): Message to decrypt

        Returns:
            str: Decrypted message
        """
        return "".join([chr(pow(c, self._d, self._n)) for c in cipher_text])

    def _generate_keys(self, num_bits: int = N_BITS) -> tuple[int, int, int]:
        """
        Generate public and private keys

        Args:
            num_bits (int, optional): Number of bits; defaults to N_BITS

        Returns:
            tuple[int, int, int]: Values used for public and private keys
        """
        p, q = self._generate_primes(num_bits)
        e, n, totient = 2, (p * q), (p - 1) * (q - 1)
        
        for e in range(2, totient):
            if gcd(e, totient) == 1:
                break

        return (n, e, pow(e, -1, totient))
    
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
        if num_bits < 2:
            raise ValueError("Number of bits must be larger than 1")

        p = getPrime(num_bits)
        q = getPrime(num_bits)

        while p == q:
            p = getPrime(num_bits)
            q = getPrime(num_bits)

            if p != q:
                return p, q

        return p, q

# if __name__ == "__main__":
#     cipher = RSA()
#     msg = "TESTING"
#     print("msg =", msg)
#     encrypted = cipher.encrypt(msg)
#     print("\nencrypted =", encrypted)
#     decrypted = cipher.decrypt(encrypted)
#     print("\ndecrypted =", decrypted)