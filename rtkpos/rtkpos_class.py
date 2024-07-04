import datetime
import logging
import os
import sys
from dataclasses import dataclass, field
from typing import Tuple

import numpy as np
import pandas as pd
import polars as pl
import utm

import globalvars
from utils.gnss_dt import gpsms2dt
from utils.utilities import locate, str_red, str_yellow


@dataclass
class Rtkpos:
    """RTKPOS class"""

    pos_fn: str
    start_time: datetime.time = field(default=None)
    end_time: datetime.time = field(default=None)

    logger: logging.Logger = field(default=None)

    def __post_init__(self):
        self.validate_file()
        self.validate_start_time()
        self.validate_end_time()

    def validate_file(self):
        """validate existence of the RTK position file

        Raises:
            ValueError: when file is not accessible
        """
        if not os.path.isfile(self.pos_fn) or not os.access(self.pos_fn, os.R_OK):
            if self.logger:
                self.logger.error(f"File does not exist: {self.pos_fn}")
            raise ValueError(f"File does not exist or is not accessible: {self.pos_fn}")

        if self.logger:
            self.logger.info(f"File validated successfully: {self.pos_fn}")

    def validate_start_time(self):
        """validate if the argument is instance of datetime.time

        Raises:
            ValueError: if not valid datetime.time object
        """
        if self.start_time is not None:
            if not isinstance(self.start_time, datetime.time):
                self.logger.error(
                    f"Invalid start_time {self.start_time}: not a valid datetime.time object."
                )
                raise ValueError(
                    f"Invalid start_time {self.start_time}: not a valid datetime.time object."
                )
            else:
                self.logger.info(
                    f"Start time {self.start_time} validated successfully."
                )
        else:
            self.logger.info("No start time specified.")

    def validate_end_time(self):
        """validate if the argument is instance of datetime.time

        Raises:
            ValueError: if not valid datetime.time object
        """
        if self.end_time is not None:
            if not isinstance(self.end_time, datetime.time):
                self.logger.error(
                    f"Invalid end_time {self.end_time}: not a valid datetime.time object."
                )
                raise ValueError(
                    f"Invalid end_time {self.end_time}: not a valid datetime.time object."
                )
            else:
                self.logger.info(f"end time {self.end_time} validated successfully.")
        else:
            self.logger.info("No end time specified.")

    def read_pos_file(self) -> pl.DataFrame:
        """read the RTK position file

        Returns:
            polars.DataFrame: RTK position data
        """
        # get the processing information
        processing_info, col_names = self.info_processing()
        # print(f"processing_info = \n{processing_info}")
        # print(f"col_names = \n{col_names}")

        # get the schema for the RTK position dataframe
        pos_schema = self.rtkpos_schema()
        # print(f"pos_schema = \n{pos_schema}")

        # read the position file skipping the lines with '%'
        try:
            pos_df = pl.scan_csv(
                self.pos_fn,
                has_header=False,
                separator=",",
                comment_prefix="%",
                with_column_names=lambda names: col_names,
                schema_overrides=pos_schema,
            )
        except Exception as e:
            self.logger.error(f"Error reading file {self.pos_fn}: {e}")
            raise e

        with pl.Config(tbl_cols=-1):
            print(f"pos_df = \n{pos_df.collect()}")
        sys.exit(7)

        # get the keys from this schema as a list
        pos_headers = list(pos_schema.keys())
        print(f"pos_headers = \n{pos_headers}")

        # add the header to the dataframe

        return pos_df

    def rtkpos_schema(self) -> dict:
        """determines header and dtypes to the dataframe

        Returns:
            dict: schema for the RTK position dataframe
        """
        col_types = {
            pl.Int32: ["WNc"],
            pl.Float64: [
                "TOW(s)",
                "latitude(deg)",
                "longitude(deg)",
                "height(m)",
            ],
            pl.Int16: ["Q", "ns"],
            pl.Float32: [
                "sdn(m)",
                "sde(m)",
                "sdu(m)",
                "sdne(m)",
                "sdeu(m)",
                "sdun(m)",
                "age(s)",
                "ratio",
            ],
        }

        pos_schema = {}
        for dtype, columns in col_types.items():
            for col in columns:
                pos_schema[col] = dtype

        # print(pos_schema)

        return pos_schema

    def info_processing(self) -> Tuple[dict, list]:
        """extracts the processing information from the header lines

        Returns:
            dict: processing information
            list: names of columns
        """
        # read from the position file line per line until the line no longer starts with '%'
        # to get processing information
        hdr_lines = []
        with open(self.pos_fn, "r") as f:
            line = f.readline()
            while line.startswith("%"):
                hdr_lines.append(line)
                line = f.readline()

        counter = 0
        info_processing = {}
        # go over the lines that contain ":" and extract the information
        for line in hdr_lines:
            if ":" in line:
                # split the line into key and value and strip the whitespace
                key_val = line.split(":", 1)
                key = key_val[0].strip()[2:]
                val = key_val[1].strip()

                if key.startswith("("):
                    pass
                elif not key.startswith("inp file"):
                    info_processing[key] = val
                else:
                    info_processing[f"{key}-{counter}"] = val
                    counter += 1
            else:  # line holding the column names
                col_names = line.split(",")

        # rename the 'inp file' parts to reflect rover and base obs and nav files
        if counter == 2:
            info_processing["rover_obs"] = info_processing.pop("inp file-0")
            info_processing["brdc_nav"] = info_processing.pop("inp file-1")
        else:
            info_processing["rover_obs"] = info_processing.pop("inp file-0")
            info_processing["base_obs"] = info_processing.pop("inp file-1")
            info_processing["brdc_nav"] = info_processing.pop("inp file-2")

        # treat the column names to get the correct list of column names
        col_names = [col.strip() for col in col_names]
        col_names = ["WNc", "TOW(s)"] + col_names[1:]
        # print(f"column names = \n{col_names}")

        # print(f"info_processing = \n{info_processing}")
        return info_processing, col_names
