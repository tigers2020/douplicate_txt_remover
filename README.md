# File Duplicate Remover

This project is a Python-based tool to identify and remove duplicate text files from a specified directory. It also moves any zip files to a designated folder. The tool compares file names and contents to determine duplicates and logs the process.

## Features

- Compares file names and contents to identify duplicates
- Moves duplicate files to a `Duplicated` folder
- Moves zip files to a `Zip` folder
- Logs each step of the process with color-coded messages

## Requirements

- Python 3.6 or higher
- `colorlog` library

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/tigers2020/douplicate_txt_remover.git
    cd douplicate_txt_remover
    ```

2. Set up a virtual environment and activate it:
    ```sh
    python -m venv .venv
    .venv\Scripts\activate  # On Windows
    source .venv/bin/activate  # On macOS/Linux
    ```

3. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. Place your text files in the `Documents` folder.

2. Run the tool using the provided batch file:
    ```sh
    run_file_manager.bat
    ```

3. Optionally, you can run the Python script directly:
    ```sh
    python file_manager.py [path_to_documents_folder]
    ```

    If the path to the documents folder is not provided, it defaults to the `Documents` folder in the script's directory.

## Logging

Logs are stored in `file_manager.log` and are also displayed in the console with color-coded messages for easier reading.

## Example

```sh
python file_manager.py Documents
