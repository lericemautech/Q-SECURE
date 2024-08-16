<div align="center">
   <h1>Q-SECURE: Quantum-Secure Protocol</h1>
   <img alt="Python" src="https://img.shields.io/static/v1?label=Language&style=flat&message=Python+3.12.2&logo=python&color=c7a228&labelColor=393939&logoColor=c7a228">
   <img alt="Git" src="https://img.shields.io/static/v1?label=Version+Control&style=flat&message=Git&logo=git&color=f05032&labelColor=393939&logoColor=f05032">
   <img alt="SymPy" src="https://img.shields.io/static/v1?label=Package&style=flat&message=SymPy&logo=sympy&color=9582b3&labelColor=393939&logoColor=9582b3">
   <img alt="NumPy" src="https://img.shields.io/static/v1?label=Package&style=flat&message=NumPy&logo=numpy&color=4d707b&labelColor=393939&logoColor=4d707b">
   <img alt="Anaconda" src="https://img.shields.io/static/v1?label=Package+Manager&style=flat&message=Conda&logo=anaconda&color=44a833&labelColor=393939&logoColor=44a833">
   <p>Implementation of multi-party computation (MPC), a quantum-resistant cryptographic algorithm, with custom client-server software to securely compute the product of <code>N</code> massive matrices.<br>Refer to <a href="#system-design">System Design</a> for further details.</p>
</div>

## Requirements
- [x] [Anaconda](https://docs.continuum.io/free/anaconda/install) **OR** [Miniconda](https://docs.conda.io/projects/miniconda/en/latest)
> [!TIP]
> If you have trouble deciding between Anaconda and Miniconda, please refer to the table below:
> <table>
>  <thead>
>   <tr>
>    <th><center>Anaconda</center></th>
>    <th><center>Miniconda</center></th>
>   </tr>
>  </thead>
>  <tbody>
>   <tr>
>    <td>New to conda and/or Python</td>
>    <td>Familiar with conda and/or Python</td>
>   </tr>
>   <tr>
>    <td>Not familiar with using terminal and prefer GUI</td>
>    <td>Comfortable using terminal</td>
>   </tr>
>   <tr>
>    <td>Like the convenience of having Python and 1,500+ scientific packages automatically installed at once</td>
>    <td>Want fast access to Python and the conda commands and plan to sort out the other programs later</td>
>   </tr>
>   <tr>
>    <td>Have the time and space (a few minutes and 3 GB)</td>
>    <td>Don't have the time or space to install 1,500+ packages</td>
>   </tr>
>   <tr>
>    <td>Don't want to individually install each package</td>
>    <td>Don't mind individually installing each package</td>
>   </tr>
>  </tbody>
> </table>
>
> Typing out entire Conda commands can sometimes be tedious, so I wrote a shell script ([`conda_shortcuts.sh` on GitHub Gist](https://gist.github.com/lynkos/7a4ce7f9e38bb56174360648461a3dc8)) to define shortcuts for commonly used Conda commands.
> <details>
>   <summary>Example: Delete/remove a conda environment named <code>test_env</code></summary>
>
> * Shortcut command
>     ```
>     rmenv test_env
>     ```
> * Manually typing out the entire command
>     ```sh
>     conda env remove -n test_env && rm -rf $(conda info --base)/envs/test_env
>     ```
>
> The shortcut has 80.8% fewer characters!
> </details>

## Usage
1. Verify that conda is installed
   ```sh
   conda --version
   ```
2. Ensure conda is up to date
   ```sh
   conda update conda
   ```
3. Enter the the directory where you want the repository (`Q-SECURE`) to be cloned
    * UNIX
        ```sh
        cd ~/path/to/directory
        ```
    * Windows
        ```sh
        cd C:\path\to\directory
        ```
4. Clone the repository, then enter its directory
    ```sh
    git clone https://github.com/lericemautech/Q-SECURE.git && cd Q-SECURE
    ```
5. Create a conda virtual environment from `environment.yml`
   ```sh
   conda env create -f environment.yml
   ```
6. Activate the virtual environment (`q-secure_env`)
   ```sh
   conda activate q-secure_env
   ```
7. Confirm that the virtual environment (`q-secure_env`) is active
     * If active, the virtual environment's name should be in parentheses () or brackets [] before your command prompt, e.g.
       ```
       (q-secure_env) $
       ```
     * If necessary, see which environments are available and/or currently active (active environment denoted with asterisk (*))
       ```sh
       conda info --envs
       ```
       **OR**
       ```sh
       conda env list
       ```
8. Run the 1st, 2nd, and 3rd servers within `Q-SECURE` directory
   ```py
   python -m project.test.TestServer1
   python -m project.test.TestServer2
   python -m project.test.TestServer3
   ```
9. Run the client within `Q-SECURE` directory
   ```py
   python -m project.src.Client
   ```
10. Press `CTRL + C` in the terminal running each server to disconnect

## System Design
1. Split each of `N` massive matrices into submatrices
2. Homomorphically encrypt the submatrices and disperse evenly among `M` Internet of Things (IoT) devices
3. `M` IoT devices calculate the product of `N` homomorphically encrypted submatrices and send the result back upon completion
4. Received submatrices (i.e. results) are decrypted and concatenated into a single matrix, which is the final result

<div align="center">
   <img alt="MPC System Design" src="https://media.licdn.com/dms/image/v2/D4E2DAQEm3J4NVypV1Q/profile-treasury-image-shrink_800_800/profile-treasury-image-shrink_800_800/0/1723823236619?e=1724428800&v=beta&t=g5L7EZ_4hHJc2qbV9pGKdI8-0MIGNdHIaj3nU4JqSqc">
</div>
