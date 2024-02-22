from mpyc.runtime import mpc
from numpy import random, vectorize

MIN = 0                           # Min value in the matrix
MAX = 5                           # Max value in the matrix
VALUES_SIZE = 2 ** 8              # Number of bits in secure integers
SECINT = mpc.SecInt(VALUES_SIZE)  # Secure VALUES_SIZE-bit integer for secret values

@mpc.coroutine
async def generate_random_secure_matrix(length: int, width: int, senders: int = 0):
    """
    Generates a random, encrypted matrix of size length * width

    Args:
        length (int): Length of matrix
        width (int): Width of matrix
        senders (int): Number of senders; defaults to 0
    """
    U = random.randint(MIN, MAX, size = (length, width), dtype = int)
    print(f"Pre-encrypted Matrix =\n{U}\n")
    
    U = vectorize(lambda a: SECINT(int(a)))(U).tolist()
    print(f"Encrypted Matrix =\n{U}\n")
    
    U = await mpc.transfer(U, senders = senders)
    return U

async def main():
    await mpc.start()

    print(f"\nMATRIX A:\n")
    A = generate_random_secure_matrix(8, 8)

    print(f"MATRIX B:\n")
    B = generate_random_secure_matrix(8, 2)
        
    L = mpc.matrix_prod(A, B)
    print(f"Matrix A * Matrix B =\n{L}\n")
    
    await mpc.shutdown()

if __name__ == "__main__":
    mpc.run(main())

