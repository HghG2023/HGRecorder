from datetime import datetime
import random
from pathlib import Path
from dotenv import load_dotenv
from typing import Union
import os

load_dotenv()

def check_dir(dir_path: Union[str, Path]) -> str:
    """
    Ensure a directory exists, creating it if necessary.

    Parameters
    ----------
    dir_path : str or Path
        The path to the directory to check.

    Returns
    -------
    dir_path : str
        The path to the directory, after ensuring it exists.
    """
    Path(dir_path).mkdir(parents=True, exist_ok=True)
    return str(dir_path)

def today(splitstr="-") -> str:
    """
    Get today's date as a string in the format "YYYY-MM-DD"

    Parameters
    ----------
    splitstr : str, optional
        The string to use as the separator between the year, month, and day. Defaults to "-".

    Returns
    -------
    str
        Today's date as a string in the specified format.
    """
    return datetime.now().strftime(f'%Y{splitstr}%m{splitstr}%d')


if __name__ == "__main__":
    print(today())
 
