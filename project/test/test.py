# This file is used to test the code in the src folder
from timeit import timeit
from project.src.Shared import generate_matrix

SHOTS = 1000
SIG_FIGS = 5
LENGTH = 8
HORIZONTAL_PARTITIONS = 2
VERTICAL_PARTITIONS = 2

def timing(func: str, setup: str, sims: int = SHOTS) -> float:
    """
    Define general timing function for simulations

    Args:
        func (str): Function to simulate
        setup (str): Necessary imports and variables
        sims (int, optional): Number of simulations; defaults to SHOTS

    Returns:
        float: Average calculation time (in milliseconds) for func after simulations
    """
    return timeit(func, f"from __main__ import {setup}", number = sims) * 1000
    
def simulations() -> None:
    """
    Runs simulations for:
    
    (1) Individual steps in calculate_result()
    (2) Calculation types (i.e. calculate_result(), matmul(), einsum())

    Prints their results and determines the quickest calculation
    """
    # Input and imports strings for timing
    matrix_1 = "np.random.randint(MIN, MAX, size = (LENGTH, LENGTH))"
    matrix_2 = "np.random.randint(MIN, MAX, size = LENGTH)"
    input = f"{matrix_1}, {matrix_2}"
    imports = "np, MIN, MAX, LENGTH"
    
    # Simulate calculations for each method of matrix multiplication
    c_time = timing(f"calculate_result({input})", f"{imports}, calculate_result")
    m_time = timing(f"np.matmul({input})", imports)
    e_time = timing(f"np.einsum('ij,j->i', {input})", imports)
    
    # Print time calculations
    print("calculate_result() Time =", round(c_time, SIG_FIGS), "ms")
    print("Matmul Calculation Time =", round(m_time, SIG_FIGS), "ms")
    print("Einsum Calculation Time =", round(e_time, SIG_FIGS), "ms")
    
    # Determine quickest calculation
    minimum = min(e_time, c_time, m_time)
    if minimum == e_time: print("\nEinsum is %f ms faster than calculate_result()" % round(abs(c_time - e_time), SIG_FIGS))
    elif minimum == m_time: print("\nMatmul is %f ms faster than calculate_result()" % round(abs(c_time - m_time), SIG_FIGS))
    else: print("\ncalculate_result() is the fastest calculation!")

if __name__ == "__main__":
    m1 = generate_matrix(LENGTH, LENGTH)
    m2 = generate_matrix(LENGTH, 3)

    from psutil import virtual_memory

    print(f"{virtual_memory().available / 1000000000:.2f} GB")