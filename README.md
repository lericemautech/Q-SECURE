# Q-SECURE: Quantum-Secure Protocol
![](https://img.shields.io/static/v1?label=Language&style=flat&message=Python+3.12.0&logo=python&color=c7a228&labelColor=393939&logoColor=c7a228)
![](https://img.shields.io/static/v1?label=Package&style=flat&message=NumPy&logo=numpy&color=4d707b&labelColor=393939&logoColor=4d707b)
![](https://img.shields.io/static/v1?label=Package+Manager&style=flat&message=Conda&logo=anaconda&color=44a833&labelColor=393939&logoColor=44a833)
![](https://img.shields.io/static/v1?label=Version+Control&style=flat&message=Git&logo=git&color=f05032&labelColor=393939&logoColor=f05032)
![](https://img.shields.io/static/v1?label=IDE&style=flat&message=Visual+Studio+Code&logo=visual+studio+code&color=007acc&labelColor=393939&logoColor=007acc)

## Requirements
- [x] [Python 3.12.0](https://www.python.org/downloads)
- [x] [NumPy](https://numpy.org/install)
- [x] [Git](https://git-scm.com/downloads)

## Usage
1. Enter the the directory where you want the repository (`Q-SECURE`) to be cloned
    * UNIX
        ```
        cd ~/path/to/directory
        ```
    * Windows
        ```
        cd C:\path\to\directory
        ```
2. Clone the repository, then enter its directory
    ```
    git clone https://github.com/lericemautech/Q-SECURE.git && cd Q-SECURE
    ```
3. Run the 1st server:
    * UNIX
        ```
        $(which python) -m project.test.TestServer1
        ```
    * Windows
        ```
        $(where python) -m project.test.TestServer1
        ```
4. Run the 2nd server:
    * UNIX
        ```
        $(which python) -m project.test.TestServer2
        ```
    * Windows
        ```
        $(where python) -m project.test.TestServer2
        ```
5. Run the 3rd server:
    * UNIX
        ```
        $(which python) -m project.test.TestServer3
        ```
    * Windows
        ```
        $(where python) -m project.test.TestServer3
        ```
6. Run the client
    * UNIX
        ```
        $(which python) -m project.src.Client
        ```
    * Windows
        ```
        $(where python) -m project.src.Client
        ```
7. Press `CTRL + C` in the terminal running each server to disconnect