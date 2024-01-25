<div align="center">
<h1>Q-SECURE: Quantum-Secure Protocol</h1>
<img alt="Python" src="https://img.shields.io/static/v1?label=Language&style=flat&message=Python+3.12.0&logo=python&color=c7a228&labelColor=393939&logoColor=c7a228">
<img alt="Git" src="https://img.shields.io/static/v1?label=Version+Control&style=flat&message=Git&logo=git&color=f05032&labelColor=393939&logoColor=f05032">
<img alt="NumPy" src="https://img.shields.io/static/v1?label=Package&style=flat&message=NumPy&logo=numpy&color=4d707b&labelColor=393939&logoColor=4d707b">
<img alt="Anaconda" src="https://img.shields.io/static/v1?label=Package+Manager&style=flat&message=Conda&logo=anaconda&color=44a833&labelColor=393939&logoColor=44a833">
<img alt="IDE" src="https://img.shields.io/static/v1?label=IDE&style=flat&message=Visual+Studio+Code&logo=visual+studio+code&color=007acc&labelColor=393939&logoColor=007acc">
</div>

## Requirements
- [x] [Anaconda](https://docs.continuum.io/free/anaconda/install) **OR** [Miniconda](https://docs.conda.io/projects/miniconda/en/latest)
> [!NOTE]
> If you have trouble deciding between Anaconda and Miniconda, please refer to the table below
> <table>
> <thead>
> <tr>
> <th><center>Anaconda</center></th>
> <th><center>Miniconda</center></th>
> </tr>
> </thead>
> <tbody>
> <tr>
> <td>New to conda and/or Python</td>
> <td>Familiar with conda and/or Python</td>
> </tr>
> <tr>
> <td>Like the convenience of having Python and 1,500+ scientific packages automatically installed at once</td>
> <td>Want fast access to Python and the conda commands and plan to sort out the other programs later</td>
> </tr>
> <tr>
> <td>Have the time and space (a few minutes and 3 GB)</td>
> <td>Don't have the time or space to install 1,500+ packages</td>
> </tr>
> <tr>
> <td>Don't want to individually install each package</td>
> <td>Don't mind individually installing each package</td>
> </tr>
> </tbody>
> </table>

## Usage
1. Verify that conda is installed
   ```
   conda --version
   ```
2. Ensure conda is up to date
   ```
   conda update conda
   ```
3. Enter the the directory where you want the repository (`Q-SECURE`) to be cloned
    * UNIX
        ```
        cd ~/path/to/directory
        ```
    * Windows
        ```
        cd C:\path\to\directory
        ```
4. Clone the repository, then enter its directory
    ```
    git clone https://github.com/lericemautech/Q-SECURE.git && cd Q-SECURE
    ```
5. Create a conda virtual environment from `environment.yml`
   ```
   conda env create -f environment.yml
   ```
6. Activate the virtual environment (`q-secure_env`)
   ```
   conda activate q-secure_env
   ```
7. Confirm that the virtual environment (`q-secure_env`) is active
     * If active, the virtual environment's name should be in parentheses () or brackets [] before your command prompt, e.g.
       ```
       (q-secure_env) $
       ```
     * If necessary, see which environments are available and/or currently active (active environment denoted with asterisk (*))
       ```
       conda info --envs
       ```
       **OR**
       ```
       conda env list
       ```
8. Run the 1st server within `Q-SECURE` directory
    * UNIX
        ```
        $(which python) -m project.test.TestServer1
        ```
    * Windows
        ```
        $(where python) -m project.test.TestServer1
        ```
9. Run the 2nd server within `Q-SECURE` directory
    * UNIX
        ```
        $(which python) -m project.test.TestServer2
        ```
    * Windows
        ```
        $(where python) -m project.test.TestServer2
        ```
10. Run the 3rd server within `Q-SECURE` directory
    * UNIX
        ```
        $(which python) -m project.test.TestServer3
        ```
    * Windows
        ```
        $(where python) -m project.test.TestServer3
        ```
11. Run the client within `Q-SECURE` directory
    * UNIX
        ```
        $(which python) -m project.src.Client
        ```
    * Windows
        ```
        $(where python) -m project.src.Client
        ```
12. Press `CTRL + C` in the terminal running each server to disconnect