import datetime
import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from io import StringIO
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
        """Validates that the RINEX file specified in `self.rnx_fn` exists
        and is a valid RINEX observation file.
        If the file does not exist or is not a valid RINEX observation file,
        it raises a `ValueError` with an appropriate error message,
        and logs the error using the provided `self.logger` object if it is not `None`.
        """
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
        """
        Validates the GNSS systems specified in `self.gnss`.

        If `self.gnss` is `None`, logs an informational message and returns.

        Otherwise, converts the input string to uppercase and checks if each character
        is a valid GNSS system code (as defined in `GNSS_DICT`). If any invalid systems
        are found, logs an error message and raises a `ValueError`.

        If all systems are valid, stores the validated list of GNSS systems in `self.gnss`
        and logs an informational message.
        """
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
        """
        Validates the start time of the RINEX data.

        If `self.start_time` is not `None`, checks if it is a valid `datetime.time` object.
            If not, logs an error message and raises a `ValueError`.
        If `self.start_time` is `None`, logs an informational message.
        If `self.start_time` is a valid `datetime.time` object, logs an informational message.
        """

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
        """
        Validates the end time of the RINEX data.

        If `self.end_time` is not `None`, checks if it is a valid `datetime.time` object.
            If not, logs an error message and raises a `ValueError`.
        If `self.end_time` is `None`, logs an informational message.
        If `self.end_time` is a valid `datetime.time` object, logs an informational message.
        """

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
        """
        Validates the logging level for the console handler in the logger.

        If a logger is provided, this method retrieves the logging level for the
        console handler (i.e. the handler that writes to stdout or stderr) and
        stores it in the `_console_loglevel` attribute.

        It then logs an informational message with the console log level.
        """

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
            logger (Logger): logger utility

        Returns:
            dict: dict of dataframes per GNSS containing the tab_obs view of the RINEX observation file
        """
        # locate gfzrnx
        gfzrnx_exe = locate("gfzrnx")

        # Check executable permissions for gfzrnx
        if not os.access(gfzrnx_exe, os.X_OK):
            if self.logger:
                self.logger.error(f"No execute permission for gfzrnx at: {gfzrnx_exe}")
            raise PermissionError(f"No execute permission for gfzrnx at: {gfzrnx_exe}")

        # Check read permissions for input RINEX file
        if not os.access(self.rnx_fn, os.R_OK):
            if self.logger:
                self.logger.error(f"No read permission for RINEX file: {self.rnx_fn}")
            raise PermissionError(f"No read permission for RINEX file: {self.rnx_fn}")

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
            output_buffer = StringIO(result.stdout)

            # Store just the headers initially
            headers = {}

            # First pass to get headers
            for line in output_buffer:
                if line.startswith("#HD"):
                    parts = line.strip().split(",")
                    sys = parts[1].strip("'")
                    headers[sys] = [h.strip("'") for h in parts[2:]]

            # Reset buffer position
            output_buffer.seek(0)

            # Create streaming dataframes for each system
            result_dfs = {}
            for sys in self.gnss:
                if sys in headers:
                    # Create a generator for the data
                    def data_generator():
                        for line in output_buffer:
                            if line.startswith("OBS"):
                                parts = line.strip().split(",")
                                if parts[1].strip("'") == sys:
                                    yield [
                                        val.strip("'") if val.strip("'") else None
                                        for val in parts[2:]
                                    ]
                        output_buffer.seek(0)

                    # Create DataFrame using streaming
                    df = (
                        pl.DataFrame(
                            data_generator(), schema=headers[sys], orient="row"
                        )
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

            output_buffer.close()
            return result_dfs

        except subprocess.CalledProcessError as e:
            if self.logger:
                self.logger.error(f"gfzrnx conversion failed: {e.stderr}")
            raise RuntimeError(f"gfzrnx conversion failed: {e.stderr}")
        except PermissionError as e:
            if self.logger:
                self.logger.error(f"Permission error running gfzrnx: {str(e)}")
            raise PermissionError(f"Permission error running gfzrnx: {str(e)}")

    def tabobs_to_csv(self, result_dfs: dict) -> pl.DataFrame:
        """converts the tabular observation file to polars dataframe with 1 observation per row

        Args:
            result_dfs (dict): contains the tabular observation dataframes per GNSS system

        Returns:
            pl.DataFrame: dataframe containing the tabular observation data in CSV format
        """
        # Process all frequency/signal combinations in one pass
        csv_rows = []
        for gnss_type, df in result_dfs.items():
            # Get frequency/signal combinations
            freq_sigs = {
                (col[1], col[2])
                for col in df.columns
                if len(col) == 3 and col[0] in ["C", "L", "D", "S"]
            }

            # Create a single transformation for all freq/sigs
            transforms = []
            for freq, sigt in freq_sigs:
                transforms.append(
                    pl.DataFrame(
                        {
                            "GNSS": gnss_type,
                            "WKNR": df["WKNR"],
                            "TOW": (df["TOW"] * 1000)
                            .round()
                            .cast(pl.Int64),  # Explicit casting to Int64
                            "PRN": df["PRN"].str.extract(r"(\d+)"),
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
                        pl.all_horizontal(
                            [pl.col(col).is_not_null() for col in ["C", "L", "D", "S"]]
                        )
                    )
                    .collect()
                )

            csv_rows.extend(transforms)

        # Combine and sort in one operation
        return pl.concat(csv_rows).sort(["WKNR", "TOW", "GNSS", "PRN", "cfreq", "sigt"])
