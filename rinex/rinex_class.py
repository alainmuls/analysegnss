import datetime
import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from io import StringIO
from icecream import ic
import polars as pl

from config import GNSS_DICT
from utils.utilities import locate, str_red, str_green


@dataclass
class RINEX:
    """class for RINEX files"""

    rnx_fn: str = field(default=None, metadata={"help": "RINEX file name"})
    gnss: str = field(default=None, metadata={"help": "select multiple from GREC"})

    start_time: datetime.time = field(default=None, metadata={"help": "start time"})
    end_time: datetime.time = field(default=None, metadata={"help": "end time"})

    logger: logging.Logger = field(default=None, metadata={"help": "logger object"})
    _console_loglevel: int = field(
        default=logging.ERROR, metadata={"help": "console log level"}
    )

    def __post_init__(self):
        self.validate_file()
        self.validate_gnss()
        self.validate_start_time()
        self.validate_end_time()
        self.validate_logger_level()

    def validate_file(self):
        if not os.path.isfile(self.rnx_fn):
            if self.logger:
                self.logger.error(f"File does not exist: {self.rnx_fn}")
            raise ValueError(f"File does not exist: {self.rnx_fn}")

        # check if it is a RINEX observation file
        try:
            with open(self.rnx_fn, "r") as file:
                # Read the first line of the file
                first_line = file.readline().strip()

                # Check if it matches the RINEX observation file format
                if not (
                    "OBSERVATION DATA" in first_line
                    and "RINEX VERSION / TYPE" in first_line
                ):
                    if self.logger is not None:
                        self.logger.error(
                            f"File is not a RINEX observation file: {self.rnx_fn}"
                        )
                    raise ValueError(
                        f"File is not a RINEX observation file: {self.rnx_fn}"
                    )
        except Exception as e:
            if self.logger is not None:
                self.logger.error(f"Error reading file: {e}")
            raise ValueError(f"Error reading file: {e}")

    def validate_gnss(self):
        if self.gnss is None:
            if self.logger:
                self.logger.info("No GNSS systems specified.")
            return

        # Convert input string to uppercase and list of characters
        gnss_list = list(self.gnss.upper())

        # Check if each character is in GNSS_DICT
        invalid_systems = [sys for sys in gnss_list if sys not in GNSS_DICT]

        if invalid_systems:
            error_msg = f"Invalid GNSS system(s): {','.join(invalid_systems)}. "
            f"Valid systems are: {','.join(GNSS_DICT.keys())}"
            if self.logger:
                self.logger.error(error_msg)
            raise ValueError(error_msg)

        # Store the validated list of GNSS systems
        self.gnss = gnss_list

        if self.logger:
            self.logger.info(
                f"GNSS systems validated successfully: {','.join(self.gnss)}"
            )

    def validate_start_time(self):
        if self.start_time is not None:
            if not isinstance(self.start_time, datetime.time):
                if self.logger:
                    self.logger.error(
                        f"Invalid start_time {self.start_time}: not a valid datetime.time object."
                    )
                raise ValueError(
                    f"Invalid start_time {self.start_time}: not a valid datetime.time object."
                )
            else:
                if self.logger:
                    self.logger.info(
                        f"Start time {self.start_time} validated successfully."
                    )
        else:
            if self.logger:
                self.logger.info("No start time specified.")

    def validate_end_time(self):
        if self.end_time is not None:
            if not isinstance(self.end_time, datetime.time):
                if self.logger:
                    self.logger.error(
                        f"Invalid end_time {self.end_time}: not a valid datetime.time object."
                    )
                raise ValueError(
                    f"Invalid end_time {self.end_time}: not a valid datetime.time object."
                )
            else:
                if self.logger:
                    self.logger.info(
                        f"end time {self.end_time} validated successfully."
                    )
        else:
            if self.logger:
                self.logger.info("No end time specified.")

    def validate_logger_level(self):
        if self.logger is not None:
            # get the logging level for the console
            for handler in self.logger.handlers:
                if isinstance(handler, logging.StreamHandler) and handler.stream in (
                    sys.stdout,
                    sys.stderr,
                ):
                    # self._console_loglevel = logging.getLevelName(handler.level)
                    self._console_loglevel = handler.level

            self.logger.info(
                "Console log level set to "
                + f"{str_red(logging.getLevelName(self._console_loglevel))}"
            )

    def gfzrnx_tabobs(self) -> dict:
        """Convert RINEX observation file to tab_obs file using gfzrnx

        Args:
            rinex_fn (str): RINEX observation file name
            logger (Logger): logger utility

        Returns:
            dict: dict of dataframes per GNSS containing the tab_obs view of the RINEX observation file
        """
        # locate gfzrnx
        gfzrnx_exe = locate("gfzrnx")

        # create the tabobs name by changing the extension of the rinex_fn
        tabobs_fn = os.path.splitext(self.rnx_fn)[0] + ".tabobs"

        gfzrnx_args = [
            gfzrnx_exe,
            "-f",  # overwrite previous version of the output file
            "-finp",
            self.rnx_fn,
            "-tab",
            "-tab_sep",
            "','",
            "-tab_date",
            "wwwwd",
            "-tab_time",
            "sod",
            # "-fout",
            # tabobs_fn,
        ]

        # Add GNSS system filter if specified
        if self.gnss:
            gfzrnx_args.extend(["-satsys", "".join(self.gnss)])

        # Add time window if specified
        if self.start_time:
            gfzrnx_args.extend(["-ts", self.start_time.strftime("%H:%M:%S")])
        if self.end_time:
            gfzrnx_args.extend(["-te", self.end_time.strftime("%H:%M:%S")])

        if self.logger is not None:
            self.logger.debug(f"gfzrnx args: {' '.join(gfzrnx_args)}")

        # Run gfzrnx and capture output
        try:
            result = subprocess.run(
                gfzrnx_args, capture_output=True, text=True, check=True
            )

            if self.logger:
                self.logger.info("gfzrnx conversion successful")

            # Split output into lines
            lines = result.stdout.split("\n")

            # Initialize storage for headers and data
            headers = {}
            data = {sys: [] for sys in self.gnss}

            # Process each line
            for line in lines:
                if not line.strip():
                    continue

                parts = line.strip().split(",")
                line_type = parts[0].strip("'")
                sys = parts[1].strip("'")

                if line_type == "#HD":
                    headers[sys] = parts[2:]  # Store header for this system
                elif line_type == "OBS":
                    data[sys].append(parts[2:])  # Store data for this system

            # Create dataframe for each system
            result_dfs = {}
            for sys in self.gnss:
                if sys in headers and data[sys]:
                    if self.logger is not None:
                        self.logger.debug(f"headers for {sys}: {headers[sys]}")

                    # Strip quotes from header names and clean the data
                    clean_headers = [h.strip("'") for h in headers[sys]]
                    clean_data = [
                        [val.strip("'") if val.strip("'") else None for val in row]
                        for row in data[sys]
                    ]

                    df = (
                        pl.DataFrame(clean_data, schema=clean_headers, orient="row")
                        .lazy()
                        .with_columns(
                            [
                                pl.col("DATE").cast(pl.Int16),
                                pl.col("PRN").cast(str),
                                pl.exclude(["DATE", "PRN"]).cast(pl.Float64),
                            ]
                        )
                        .with_columns(
                            [
                                (pl.col("DATE") // 10).alias("WKNR"),
                                (pl.col("DATE") % 10 * 86400 + pl.col("TIME")).alias(
                                    "TOW"
                                ),
                            ]
                        )
                        .drop(["DATE", "TIME"])
                        .select(["WKNR", "TOW", pl.all().exclude(["WKNR", "TOW"])])
                        .collect()
                    )

                    result_dfs[sys] = df

                    if self.logger:
                        self.logger.info(
                            f"Created dataframe for system {str_green(sys)} with {str_green(len(df))} observations"
                        )

            return result_dfs

        except subprocess.CalledProcessError as e:
            if self.logger:
                self.logger.error(f"gfzrnx conversion failed: {e.stderr}")
            raise RuntimeError(f"gfzrnx conversion failed: {e.stderr}")

    def tabobs_to_csv(self, result_dfs: dict) -> pl.DataFrame:
        """Convert the gfzrnx dataframes to desired CSV format

        Args:
            result_dfs (dict): polars dataframes per GNSS system

        Returns:
            csv_df (str): combined output CSV dataframe
        """
        # disable printing with icecream
        # ic.disable()

        csv_rows = []
        for gnss_type, df in result_dfs.items():
            # Get unique frequency/signal combinations
            freq_sigs = set()
            for col in df.columns:
                if len(col) == 3 and col[0] in ["C", "L", "D", "S"]:
                    freq_sigs.add((col[1], col[2]))  # (freq, sigt)

            # Process each frequency/signal combination
            for freq, sigt in freq_sigs:
                # Create new rows for this frequency
                new_df = (
                    pl.DataFrame(
                        {
                            "GNSS": gnss_type,
                            "WKNR": df["WKNR"],
                            "TOW": df["TOW"] * 1000,  # Convert to milliseconds
                            "PRN": df["PRN"].str.extract(
                                r"(\d+)"
                            ),  # Extract number from PRN
                            "cfreq": f"L{freq}",
                            "sigt": f"{freq}{sigt}",
                            "C": df[f"C{freq}{sigt}"],
                            "L": df[f"L{freq}{sigt}"],
                            "D": df[f"D{freq}{sigt}"],
                            "S": df[f"S{freq}{sigt}"],
                        }
                    )
                    .lazy()
                    .filter(
                        pl.col("C").is_not_null()
                        & pl.col("L").is_not_null()
                        & pl.col("D").is_not_null()
                        & pl.col("S").is_not_null()
                    )
                    .collect()
                )

                with pl.Config(tbl_cols=-1):
                    ic(new_df)

                csv_rows.append(new_df)

        # Combine all dataframes
        final_df = pl.concat(csv_rows).sort(
            ["GNSS", "WKNR", "TOW", "PRN", "cfreq", "sigt"]
        )

        # sort the final dataframe by WKNR and TOW
        final_df = final_df.sort(["WKNR", "TOW"])

        # enable printing with icecream
        ic.enable()
        with pl.Config(tbl_cols=-1):
            ic(final_df)

        return final_df
