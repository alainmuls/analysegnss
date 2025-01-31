import os
import subprocess
from dataclasses import dataclass, field
from io import StringIO

import polars as pl
from rich import print

from analysegnss.config import DICT_GNSS, rich_console
from analysegnss.rinex.rinex_class import RINEX
from analysegnss.utils.utilities import str_green


@dataclass
class RINEX_OBS(RINEX):
    """class for RINEX observation files.

    It performs operations on a RINEX observation file, including reading the file,
    converting it to a tabular format, and writing it to a CSV file.
    """

    rnxobs_fn: str = field(
        default=None, metadata={"help": "RINEX observation file name"}
    )

    def __post_init__(self):
        # Keep rnxobs_fn separate from parent's rnx_fn
        super().__post_init__()
        self.validate_rnxobs_fn()

    def validate_rnxobs_fn(self):
        """Validates that the RINEX file specified in `self.rnx_fn` exists
        and is a valid RINEX observation file.
        If the file does not exist or is not a valid RINEX observation file,
        it raises a `ValueError` with an appropriate error message,
        and logs the error using the provided `self.logger` object if it is not `None`.
        """
        if not os.path.isfile(self.rnxobs_fn):
            if self.logger:
                self.logger.error(f"File does not exist: {self.rnxobs_fn}")
            raise ValueError(f"File does not exist: {self.rnxobs_fn}")

        # Validate RINEX file permissions
        if not os.access(self.rnxobs_fn, os.R_OK):
            if self.logger:
                self.logger.error(
                    f"No read permission for RINEX file: {self.rnxobs_fn}"
                )
            raise PermissionError(
                f"No read permission for RINEX file: {self.rnxobs_fn}"
            )

        # check if it is a RINEX observation file
        try:
            with open(self.rnxobs_fn, "r") as file:
                # Read the first line of the file
                first_line = file.readline().strip()

                # Check if it matches the RINEX observation file format
                if not (
                    "OBSERVATION DATA" in first_line
                    and "RINEX VERSION / TYPE" in first_line
                ):
                    if self.logger is not None:
                        self.logger.error(
                            f"File is not a RINEX observation file: {self.rnxobs_fn}"
                        )
                    raise ValueError(
                        f"File is not a RINEX observation file: {self.rnxobs_fn}"
                    )
        except Exception as e:
            if self.logger is not None:
                self.logger.error(f"Error reading file: {e}")
            raise ValueError(f"Error reading file: {e}")

    def gfzrnx_tabobs(self) -> dict:
        """Convert RINEX observation file to tab_obs file using gfzrnx

        Args:
            logger (Logger): logger utility

        Returns:
            dict: dict of dataframes per GNSS containing the tab_obs view of the RINEX observation file
        """
        # arguments for converting rinex observation file to tab_obs
        gfzrnx_args = [
            self.gfzrnx_exe,
            "-f",  # overwrite previous version of the output file
            "-finp",
            self.rnxobs_fn,
            "-tab",
            "-tab_sep",
            ",",
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
            self.logger.debug(f"running: {' '.join(gfzrnx_args)}")

        # Run gfzrnx and capture output
        try:
            # add a spinner while waiting for the conversion to complete
            with rich_console.status(
                "Please wait - Loading observations...", spinner="aesthetic"
            ):

                result = subprocess.run(
                    gfzrnx_args, capture_output=True, text=True, check=True
                )
                output_buffer = StringIO(result.stdout)
                self.logger.debug(f"gfzrnx output: \n{result.stdout[:1500]}")
                self.logger.debug(f"gfzrnx output: \n{StringIO(result.stdout[:1500])}")

                # Store just the headers initially
                headers = {}

                # First pass to get headers
                for line in output_buffer:
                    if line.startswith("#HD"):
                        parts = line.strip().split(",")
                        sys = parts[1]
                        headers[sys] = parts[2:]
                        # print(f"headers for {sys}: {headers[sys]}")
                    else:
                        break

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
                                    if parts[1] == sys:
                                        yield [
                                            val if val else None for val in parts[2:]
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
                                    (
                                        pl.col("DATE") % 10 * 86400 + pl.col("TIME")
                                    ).alias("TOW"),
                                ]
                            )
                            .drop(["DATE", "TIME"])
                            .select(["WKNR", "TOW", pl.all().exclude(["WKNR", "TOW"])])
                            .collect()
                        )

                        result_dfs[sys] = df

                        if self.logger:
                            self.logger.info(
                                f"Created dataframe for system {str_green(DICT_GNSS[sys])} with {str_green(len(df))} observations"
                            )

                output_buffer.close()

            rich_console.print("\n")

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

        # add a spinner while waiting for the conversion to complete
        with rich_console.status(
            "Please wait - converting to dataframe...", spinner="aesthetic"
        ):
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
                                "PRN": df["PRN"].str.extract(r"(\d+)").cast(pl.Int16),
                                "cfreq": f"L{freq}",
                                "sigt": f"{freq}{sigt}",

                                "C": (
                                    pl.Series([None] * len(df))
                                    if f"C{freq}{sigt}" not in df.columns
                                    else df[f"C{freq}{sigt}"]
                                ),
                                "L": (
                                    pl.Series([None] * len(df))
                                    if f"L{freq}{sigt}" not in df.columns
                                    else df[f"L{freq}{sigt}"]
                                ),
                                "D": (
                                    pl.Series([None] * len(df))
                                    if f"D{freq}{sigt}" not in df.columns
                                    else df[f"D{freq}{sigt}"]
                                ),
                                "S": (
                                    pl.Series([None] * len(df))
                                    if f"S{freq}{sigt}" not in df.columns
                                    else df[f"S{freq}{sigt}"]
                                ).cast(pl.Float32),
                            }
                        )
                        .lazy()
                        .filter(
                            pl.all_horizontal(
                                [
                                    pl.col(col).is_not_null()
                                    for col in ["C", "L", "D", "S"]
                                ]
                            )
                        )
                        .collect()
                    )

                csv_rows.extend(transforms)

        # Combine and sort in one operation
        return pl.concat(csv_rows).sort(["WKNR", "TOW", "GNSS", "PRN", "cfreq", "sigt"])
