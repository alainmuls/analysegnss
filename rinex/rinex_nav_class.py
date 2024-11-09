import os
import subprocess
from dataclasses import dataclass, field
from io import StringIO
import polars as pl
from rinex.rinex_class import RINEX

from config import GNSS_DICT
from utils.utilities import str_green


@dataclass
class RINEX_NAV(RINEX):
    """class for RINEX navigation files.

    It performs operations on a RINEX navigation file, including reading the file,
    converting it to a tabular format, and writing it to a CSV file.
    """

    rnxnav_fn: str = field(
        default=None, metadata={"help": "RINEX navigation file name"}
    )

    # Define column names for different GNSS systems
    _gnav_col_names = (
        "af0",
        "af1",
        "af2",
        "IODE",
        "Crs",
        "deltaN",
        "M0",
        "Cuc",
        "eccen",
        "Cus",
        "sqrtA",
        "toe",
        "Cic",
        "Omega0",
        "Cis",
        "Io",
        "Crc",
        "omega",
        "omegaDot",
        "IDOT",
        "CodesL2",
        "WN",
        "L2Pflag",
        "SVacc",
        "health",
        "TGD",
        "IODC",
        "toc",
        "Fit",
        "Reserved1",
        "Reserved2",
    )

    def __post_init__(self):
        # Keep rnxnav_fn separate from parent's rnx_fn
        super().__post_init__()
        self.validate_rnxnav_fn()

    def validate_rnxnav_fn(self):
        """Validates that the RINEX file specified in `self.rnx_fn` exists
        and is a valid RINEX navigation file.
        If the file does not exist or is not a valid RINEX navigation file,
        it raises a `ValueError` with an appropriate error message,
        and logs the error using the provided `self.logger` object if it is not `None`.
        """
        if not os.path.isfile(self.rnxnav_fn):
            if self.logger:
                self.logger.error(f"File does not exist: {self.rnxnav_fn}")
            raise ValueError(f"File does not exist: {self.rnxnav_fn}")

        # Validate RINEX file permissions
        if not os.access(self.rnxnav_fn, os.R_OK):
            if self.logger:
                self.logger.error(
                    f"No read permission for RINEX file: {self.rnxnav_fn}"
                )
            raise PermissionError(
                f"No read permission for RINEX file: {self.rnxnav_fn}"
            )

        # check if it is a RINEX navigation file
        try:
            with open(self.rnxnav_fn, "r") as file:
                # Read the first line of the file
                first_line = file.readline().strip()

                # Check if it matches the RINEX navigation file format
                if not (
                    "GNSS NAV DATA" in first_line
                    and "RINEX VERSION / TYPE" in first_line
                ):
                    if self.logger is not None:
                        self.logger.error(
                            f"File is not a RINEX navigation file: {self.rnxnav_fn}"
                        )
                    raise ValueError(
                        f"File is not a RINEX navigation file: {self.rnxnav_fn}"
                    )
        except Exception as e:
            if self.logger is not None:
                self.logger.error(f"Error reading file: {e}")
            raise ValueError(f"Error reading file: {e}")

    def gfzrnx_tabnav(self) -> dict:
        """Convert RINEX navigation file to tab_obs file using gfzrnx

        Args:
            logger (Logger): logger utility

        Returns:
            dict: dict of dataframes per GNSS containing the tab_obs view of the
            RINEX navigation file
        """
        # arguments for converting rinex observation file to tab_obs
        gfzrnx_args = [
            self.gfzrnx_exe,
            "-f",  # overwrite previous version of the output file
            "-finp",
            self.rnxnav_fn,
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

        try:
            result = subprocess.run(
                gfzrnx_args, capture_output=True, text=True, check=True
            )
            print(f"reulst.stdout = {result.stdout}")
            # Filter only NAV lines from result.stdout
            nav_lines = [
                line for line in result.stdout.splitlines() if line.startswith("NAV")
            ]
            # cleaned_lines = []
            # for line in nav_lines:
            #     # Remove extra quotes and commas at the end
            #     line = line.rstrip(",'")
            #     # Add quote at the start of NAV
            #     if not line.startswith("'"):
            #         line = "'" + line
            #     cleaned_lines.append(line)

            # for line in cleaned_lines[:5]:
            #     print(line)

            nav_data = "\n".join(nav_lines)
            print(f"nav_data = \n{nav_data[:5]}")

            # Read into DataFrame
            df_all_nav = pl.read_csv(
                StringIO(nav_data), has_header=False, separator=",", skip_rows=1
            )
            with pl.Config(tbl_cols=-1):
                self.logger.debug(
                    f"Converted RINEX navigation file to tabular navigation file: \n{df_all_nav}"
                )

            # Group by GNSS type (column 'S') and create dictionary of DataFrames
            nav_dict = {
                gnss_type: group_df
                for gnss_type, group_df in df_all_nav.group_by("S", maintain_order=True)
            }
            with pl.Config(tbl_cols=-1):
                for gnss, tabnav_df in nav_dict.items():
                    self.logger.debug(
                        f"Converted RINEX navigation file for {gnss} to tabular navigation file: \n{tabnav_df}"
                    )

        except subprocess.CalledProcessError as e:
            if self.logger:
                self.logger.error(f"gfzrnx conversion failed: {e.stderr}")
            raise RuntimeError(f"gfzrnx conversion failed: {e.stderr}")
        except PermissionError as e:
            if self.logger:
                self.logger.error(f"Permission error running gfzrnx: {str(e)}")
            raise PermissionError(f"Permission error running gfzrnx: {str(e)}")
