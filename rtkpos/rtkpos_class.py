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
from gnss import geoid

import globalvars
from gnss.gnss_dt import gpsms2dt
from utils.utilities import str_red


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
        else:
            self._csv_fn = self.pos_fn.replace(".pos", ".csv")

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

        # change the multiple spaces in char comma
        sed_cmd = r"sed 's/[[:blank:]]\{1,\}/,/g'"
        sed_cmd = sed_cmd + f" {self.pos_fn}"
        # print(f"sed_cmd = {sed_cmd}")
        content = os.popen(sed_cmd).read()
        with open(self._csv_fn, "w") as fd:
            fd.write(content)
        # read the position file skipping the lines with '%'
        try:
            pos_df = pl.scan_csv(
                # self.pos_fn,
                self._csv_fn,
                has_header=False,
                separator=",",
                comment_prefix="%",
                with_column_names=lambda names: col_names,
                schema_overrides=pos_schema,
            )
        except Exception as e:
            self.logger.error(f"Error reading file {self.pos_fn}: {e}")
            raise e
        
        # add columns to the dataframe
        pos_df = self.add_columns(df_pos=pos_df)

        # with pl.Config(tbl_cols=-1):
        #     print(f"pos_df = \n{pos_df.collect()}")

        return pos_df

    def rtkpos_schema(self) -> dict:
        """determines header and dtypes to the dataframe

        Returns:
            dict: schema for the RTK position dataframe
        """
        col_types = {
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
                col_names = line.split()

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
        
        col_names = ["WNc", "TOW(s)"] + col_names[2:] 

        self.logger.info(f"column names = \n{col_names}")
        self.logger.info(f"info_processing = \n{info_processing}")       
        #print(f"column names = \n{col_names}")
        # print(f"info_processing = \n{info_processing}")
        
        return info_processing, col_names

    def add_columns(self, df_pos: pl.DataFrame) -> pl.DataFrame:
        """checks if we can create a datetime, PRN, UTM columns in the dataframe

        Args:
            df_pos (pl.DataFrame): dataframe corresponding to RNX2RTKP POS file

        Returns:
            pl.DataFrame: dataframe with added information
        """
        
        # add date-time and PRN (as str) to the dataframe
        if "WNc" in df_pos.columns and "TOW(s)" in df_pos.columns:
            self.logger.info("\tadding datetime to the dataframe")
            df_pos = df_pos.with_columns(
                pl.struct(["WNc", "TOW(s)"])
                .apply(
                    lambda x: gpsms2dt(x["WNc"], x["TOW(s)"] * 1000),
                    return_dtype=datetime.datetime,
                )
                .alias("DT")
            ).lazy()
        
        # add UTM coordinates
        if "latitude(deg)" in df_pos.columns and "longitude(deg)" in df_pos.columns:
            self.logger.info("\tadding UTM coordinates to the dataframe")

            # Function to convert lat/lon in degrees to UTM
            def latlon_to_utm(lat, lon):
                easting, northing, _, _ = utm.from_latlon(lat, lon)
                return {"easting": easting, "northing": northing}

            # Apply the conversion function lazily using map_elements with specified return_dtype
            df_pos = df_pos.with_columns(
                pl.struct(["latitude(deg)", "longitude(deg)"])
                .apply(
                    lambda row: latlon_to_utm(
                        row["latitude(deg)"], row["longitude(deg)"]
                    ),
                    return_dtype=pl.Struct(
                        [
                            pl.Field("easting", pl.Float64),
                            pl.Field("northing", pl.Float64),
                        ]
                    ),
                )
                .alias("utm_coords")
            ).lazy()

            # Extract the UTM.East and UTM.North from the computed struct
            df_pos = df_pos.with_columns(
                [
                    pl.col("utm_coords").struct.field("easting").alias("UTM.E"),
                    pl.col("utm_coords").struct.field("northing").alias("UTM.N"),
                ]
            ).lazy()

            # Drop intermediate columns
            df_pos = df_pos.drop(["utm_coords"]).lazy()

        # add geoid undulation and orthometric height
        if "latitude(deg)" in df_pos.columns and "longitude(deg)" in df_pos.columns:
            self.logger.info(
                "\tadding geoid undulation & orthometric height to the dataframe"
            )
            # initialise the geodheight class
            gh_model = geoid.GeoidHeight("./gnss/geoids/egm2008-1.pgm")

            df_pos = df_pos.with_columns(
                pl.struct(["latitude(deg)", "longitude(deg)"])
                .apply(
                    lambda x: gh_model.get(
                        x["latitude(deg)"], x["longitude(deg)"], gh_model
                    ),
                    return_dtype=pl.Float64,
                )
                .alias("undulation")
            ).lazy()

            df_pos = df_pos.with_columns(
                pl.struct(["height(m)", "undulation"])
                .apply(
                    lambda x: x["height(m)"] - x["undulation"], return_dtype=pl.Float64
                )
                .alias("orthoH")
            ).lazy()

        self.logger.info(f"\tcollecting the dataframe. {str_red('Be patient.')}")
        
        try:
            df_pos = df_pos.collect()
        except pl.exceptions.ComputeError as e:
            print(f"""{str_red("""
                \r[ERROR] Probably a dtype error.
                \rCheck if RTKlib date time is set to tow and not hms.
                """)}
            """)
            self.logger.error(f"""
                \r Error collecting dataframe: {e}\n
                \rProbably a dtype error.
                \rCheck if RTKlib date time is set to tow and not hms.
            """)         
            sys.exit()
        
        return df_pos
