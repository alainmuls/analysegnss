#!/usr/bin:env python

import logging
import os
import shutil
import subprocess
import sys
from datetime import date, datetime, timedelta

import numpy as np
import polars as pl
from termcolor import colored

from analysegnss.config import ERROR_CODES

__author__ = "amuls"


def change_directory(mydir: str, name_logger: str = None) -> bool:
    """
    change_directory checks whether we can change to the specified directory 'mydir'
    """
    if name_logger is not None:
        logger = logging.getLogger(name_logger)

    try:
        os.chdir(mydir)
        if name_logger is not None:
            logger.debug(f"Current working directory: {str_green(text=os.getcwd())}")
        else:
            sys.stderr.write(
                f"Current working directory: {str_green(text=os.getcwd())}\n"
            )
        return ERROR_CODES["E_SUCCESS"]
    except FileNotFoundError:
        if name_logger is not None:
            logger.warning(f"Directory: {str_red(mydir)} does not exist")
        else:
            sys.stderr.write(f"Directory: {str_red(mydir)} does not exist\n")
        return ERROR_CODES["E_DIR_NOT_EXIST"]
    except NotADirectoryError:
        if name_logger is not None:
            logger.warning(f"{str_red(mydir)} is not a directory")
        else:
            sys.stderr.write(f"{str_red(mydir)} is not a directory\n")
        return ERROR_CODES["E_DIR_NOT_EXIST"]
    except PermissionError:
        if name_logger is not None:
            logger.warning(f"You do not have permissions to change to {str_red(mydir)}")
        else:
            sys.stderr.write(
                f"You do not have permissions to change to {str_red(mydir)}\n"
            )
        return ERROR_CODES["E_DIR_NOT_EXIST"]


def merge_dictionaries(dict1: dict, dict2: dict) -> dict:
    """
    Recursive merge dictionaries.

    :param dict1: Base dictionary to merge.
    :param dict2: Dictionary to merge on top of base dictionary, keeping values from dict1 when same key.

    :return: Merged dictionary
    """
    # print(f"\n---------------------\ndict1:\n{pprint.pformat(dict1, indent=4)}")
    # print(f"\n---------------------\ndict2:\n{pprint.pformat(dict2, indent=4)}")

    for key, val in dict1.items():
        if isinstance(val, dict):
            dict2_node = dict2.setdefault(key, {})
            merge_dictionaries(val, dict2_node)
        else:
            if key not in dict2:
                dict2[key] = val
            else:
                dict2[key] = dict1[key]

    return dict2


# def df_move_column_inplace(df: pd.DataFrame, col: str, pos: int):
#     """
#     moves a column 'col' from a dataframe 'df' to position 'pos'

#     :param df: dataframe
#     :param col: name of column to move
#     :param pos: column index to move 'col' to
#     """
#     col = df.pop(col)
#     df.insert(pos, col.name, col)


def file_len(fname: str) -> int:
    """
    counts the number of lines in a text file, using the linux program 'wc'

    :param fname: name of file
    :return: length of file (count of lines)
    """
    p = subprocess.Popen(
        ["wc", "-l", fname], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    result, err = p.communicate()
    if p.returncode != 0:
        raise IOError(err)
    return int(result.strip().split()[0])


def round_minutes(dt: datetime, direction: str, resolution: int) -> datetime:
    """
    rounds a datetime object according to the specified resolution UP or DOWN

    :param dt: datetime object to round 'up' or 'down'
    :param direction: 'up' or 'down' rounding
    :param resolution: resolution in minutes
    :return: the rounded datetime value
    """
    dt = dt.replace(second=0, microsecond=0)
    new_minute = (
        dt.minute // resolution + (1 if direction == "up" else 0)
    ) * resolution
    return dt + timedelta(minutes=new_minute - dt.minute)


def make_rgb_transparent(rgb, bg_rgb, alpha):
    """
    make a color transparent
    """
    return [alpha * c1 + (1 - alpha) * c2 for (c1, c2) in zip(rgb, bg_rgb)]


def unique_list(list1: list) -> list:
    """
    converts the list to its unique values

    :param list1: list to convert to its unique values
    :return: list comprised of unique values
    """
    x = np.array(list1)
    return np.unique(x)


def find_idx(string: str, char: str):
    """
    find all occurrences of char in string

    :param string: string object to inspect
    :param char: character to locate in string
    :return: list generator containing the indices of 'char' in 'string'
    """
    yield [i for i, c in enumerate(string) if c == char]


def find_list_idx(mylist: list, substr: str) -> list:
    """
    find_list_idx finds all indices of lines in the list which has substr as start of line
    """
    idxs = [mylist.index(line) for line in mylist if line.startswith(substr)]
    idxs.append(len(mylist))  # add so that we have closure

    return idxs


def str_green(text: str) -> str:
    """
    str_green returns the text in green

    :param text: text to color
    :return: text in green
    """
    return colored(text, "green")


def str_yellow(text: str) -> str:
    """
    str_yellow returns the text in yellow

    :param text: text to color
    :return: text in yellow
    """
    return colored(text, "yellow")


def str_magenta(text: str) -> str:
    """
    str_magenta returns the text in magenta

    :param text: text to color
    :return: text in magenta
    """
    return colored(text, "magenta")


def str_blue(text: str) -> str:
    """
    str_blue returns the text in blue

    :param text: text to color
    :return: text in blue
    """
    return colored(text, "blue")


def str_red(text: str) -> str:
    """
    str_red returns the text in red

    :param text: text to color
    :return: text in red
    """
    return colored(text, "red")


def locate(prog: str) -> str:
    """
    locate searches the PATH for the program and returns its full name

    Arguments:
        name of executable to search for
    Returns:
        full path of executable if found, else an error is raised
    Raises:
        shutil.Error: if specified program cannot be found in path
    """

    try:
        full_prog = shutil.which(prog)
    except shutil.Error as e:
        sys.stderr.write(f"Call to shutil.which gave error {str_red(e)}.\n")
        sys.exit(ERROR_CODES["E_FAILURE"])

    if full_prog is not None:
        return full_prog
    else:
        sys.stderr.write(
            f"Executable {str_red(prog)} not found in path."
            f"\n\tplease install {str_red(prog)}\n\tor adjust"
            f" your path:\n\t{os.environ['PATH']}.\n"
        )
        sys.exit(ERROR_CODES["E_MISSING_BIN"])


# def RMSE(ps: pd.Series) -> float:
#     """
#     RMSE calculates the RMSE of a pandas series containing the difference between actual and predicted values
#     """
#     if not ps.empty:
#         cs_mean = ps.mean()
#         return np.sqrt(np.square(ps - cs_mean).sum() / ps.shape[0])
#         # return np.sqrt(np.square(ps).sum() / ps.shape[0])
#     else:
#         return np.NaN


def main(argv: list):
    """
    main function starts here (only for testing), call like ``location.py sbf2rin``
    """
    print("test of locate of a program (should work on all systems)")
    print(f"\tlocate = {str_green(locate(prog='sbf2stf'))}")


# main starts here
if __name__ == "__main__":
    main(sys.argv)


def json_serial(obj):
    """
    JSON serializer for objects not serializable by default json code
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


def bin_nibble(val):
    """print binary numbers in groups of nibbles (4 bits)

    Args:
        val (int): integer value to print as binary

    Returns:
        str: binary representation grouped by 4 bits (with preceding 0)
    """
    b = bin(val)[2:]
    new_b = "_".join([b[::-1][i : i + 4][::-1] for i in range(0, len(b), 4)][::-1])
    return "".join(["0"] * (4 - len(b) % 4 if len(b) % 4 != 0 else 0) + [new_b])


def combine_dfs(dfs: dict) -> pl.DataFrame:
    """Combines  related dataframes on DateTime column

    Args:
        dfs (dict): Dictionary of PVT dataframes

    Returns:
        pl.DataFrame: Combined dataframe with all PVT information
    """
    # Start with first dataframe
    combined_df = list(dfs.values())[0]

    # Join with remaining dataframes on DT column
    for df in list(dfs.values())[1:]:
        combined_df = combined_df.join(df, on="DT", how="outer")

    return combined_df

def sf64(val, e_return_none: bool = True, logger: logging.Logger = None):
    """Safely convert to float if possible, else return original value

    Args:
        val (str): value to cast to float64
        e_return_none (bool): if True(default) None is returned if cast fails

    Returns:
        float: casted value or original value
    """
    try:
        return float(val)
    except (ValueError, TypeError):
        if logger:
            logger.debug(f"Could not cast {val} to float")
        if e_return_none:
            return None
        else:    
            return val

def si64(val, e_return_none: bool = True, logger: logging.Logger = None):
    """Safely convert to int if possible, else return original value

    Args:
        val (str): value to cast to int64
        e_return_none (bool): if True(default) None is returned if cast fails

    Returns:
        int: casted value or original value
    """
    try:
        return int(val)
    except (ValueError, TypeError):
        if logger:
            logger.debug(f"Could not cast {val} to int")
        if e_return_none:
            return None
        else:
            return val
