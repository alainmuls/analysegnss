import os
import subprocess
from dataclasses import dataclass, field
from io import StringIO
import polars as pl

from analysegnss.rinex.rinex_class import RINEX
from analysegnss.config import DICT_GNSS, rich_console
import analysegnss.rinex.rinex_column_names as rcn
from analysegnss.utils.utilities import str_green, str_red, str_yellow


@dataclass
class RINEX_NAV(RINEX):
    """RINEX Navigation File Processor

    It performs operations on a RINEX navigation file, including reading the file,
    converting it to a tabular format, and writing it to a CSV file.

    Attributes:
        rnxnav_ifn (str): Path to RINEX navigation file

    Examples:
        >>> nav = RINEX_NAV("path/to/nav.rnx")
        >>> nav_data = nav.gfzrnx_tabnav()

    """

    rnxnav_ifn: str = field(
        default=None, metadata={"help": "RINEX navigation file name"}
    )

    def __post_init__(self):
        # Keep rnxnav_ifn separate from parent's rnx_fn
        super().__post_init__()
        self.validate_rnxnav_fn()

    def validate_rnxnav_fn(self):
        """Validates that the RINEX file specified in `self.rnx_fn` exists
        and is a valid RINEX navigation file.
        If the file does not exist or is not a valid RINEX navigation file,
        it raises a `ValueError` with an appropriate error message,
        and logs the error using the provided `self.logger` object if it is not `None`.
        """
        if not os.path.isfile(self.rnxnav_ifn):
            if self.logger:
                self.logger.error(f"File does not exist: {self.rnxnav_ifn}")
            raise ValueError(f"File does not exist: {self.rnxnav_ifn}")

        # Validate RINEX file permissions
        if not os.access(self.rnxnav_ifn, os.R_OK):
            if self.logger:
                self.logger.error(
                    f"No read permission for RINEX file: {self.rnxnav_ifn}"
                )
            raise PermissionError(
                f"No read permission for RINEX file: {self.rnxnav_ifn}"
            )

        # check if it is a RINEX navigation file
        try:
            with open(self.rnxnav_ifn, "r") as file:
                # Read the first line of the file
                first_line = file.readline().strip()

                # Check if it matches the RINEX navigation file format
                if not (
                    "NAV" in first_line
                    and "DATA" in first_line
                    and "RINEX VERSION / TYPE" in first_line
                ):
                    if self.logger is not None:
                        self.logger.error(
                            f"File is not a RINEX navigation file: {self.rnxnav_ifn}"
                            f"File is not a RINEX navigation file: {self.rnxnav_ifn}"
                        )
                    raise ValueError(
                        f"File is not a RINEX navigation file: {self.rnxnav_ifn}"
                        f"File is not a RINEX navigation file: {self.rnxnav_ifn}"
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
            dict: dict of dataframes per tuple GNSS/NavType containing the tab_obs view of the
            RINEX navigation file
        """
        # arguments for converting rinex observation file to tab_obs
        gfzrnx_args = [
            self.gfzrnx_exe,
            "-f",  # overwrite previous version of the output file
            "-finp",
            self.rnxnav_ifn,
            self.rnxnav_ifn,
            "-tab",
            "-tab_sep",
            ",",
            "-tab_date",
            "wwwwd",
            "-tab_time",
            "sod",
        ]

        # Add time window if specified
        if self.start_time:
            gfzrnx_args.extend(["-ts", self.start_time.strftime("%H:%M:%S")])
        if self.end_time:
            gfzrnx_args.extend(["-te", self.end_time.strftime("%H:%M:%S")])

        if self.logger is not None:
            self.logger.debug(f"running: {' '.join(gfzrnx_args)}")

        # we have to process GLONASS apart from any other GNSS
        gnss_nav_dict = {}

        # Separate GLONASS from other GNSS systems
        other_gnss = [g for g in self.gnss if g != "R"]
        has_glonass = [g for g in self.gnss if g == "R"]

        # Add other GNSS systems first if present
        if other_gnss:
            if self.logger is not None:
                self.logger.debug(f"Processing GNSS: {other_gnss}")
            # add a spinner while waiting for the conversion to complete
            with rich_console.status(
                "Please wait - Processing GNSS:...", spinner="aesthetic"
            ):
                # process GEC systems without Glonass
                gfzrnx_args.extend(["-satsys", "".join(other_gnss)])

                # process GEC systems without Glonass
                gec_nav_dict = self.gnss_nav_to_tabnav(gfzrnx_opts=gfzrnx_args)
                gec_nav_dict = self.gnss_nav_to_tabnav(gfzrnx_opts=gfzrnx_args)
                gnss_nav_dict.update(gec_nav_dict)

            rich_console.print(f"GNSS {other_gnss} processed.")
            rich_console.print(f"GNSS {other_gnss} processed.")

        # Add GLONASS separately if present
        if has_glonass:
            # check whether we have the option "-satsys" in the gfzrnx_args,
            # if so remove it first and the following value
            if "-satsys" in gfzrnx_args:
                gfzrnx_args.remove("-satsys")
                gfzrnx_args.remove("".join(other_gnss))

            # print(f"GLONASS gfzrnx_args = {' '.join(gfzrnx_args)}")
            if self.logger is not None:
                self.logger.debug("Processing GNSS: R")
            # add a spinner while waiting for the conversion to complete
            with rich_console.status(
                "Please wait - Processing GNSS R:...", spinner="aesthetic"
            ):
                gfzrnx_args.extend(["-satsys", "R"])
                # print(f"GLONASS gfzrnx_args = {' '.join(gfzrnx_args)}")
                # Process GLONASS separately
                r_nav_dict = self.gnss_nav_to_tabnav(gfzrnx_opts=gfzrnx_args)
                if r_nav_dict is not None:
                    gnss_nav_dict.update(r_nav_dict)
                    
            rich_console.print(f"GNSS {has_glonass} processed.")
                r_nav_dict = self.gnss_nav_to_tabnav(gfzrnx_opts=gfzrnx_args)
                if r_nav_dict is not None:
                    gnss_nav_dict.update(r_nav_dict)
                    
            rich_console.print(f"GNSS {has_glonass} processed.")

        return gnss_nav_dict

    def gnss_nav_to_tabnav(self, gfzrnx_opts: list) -> dict:
    def gnss_nav_to_tabnav(self, gfzrnx_opts: list) -> dict:
        print(f"gfzrnx_opts = {gfzrnx_opts}")
        try:
            result = subprocess.run(
                gfzrnx_opts, capture_output=True, text=True, check=True
            )
            # print(f"result.stdout = {result.stdout[:1500]}")
            # print(f"result.stderr = {result.stderr[:1500]}")

        except subprocess.CalledProcessError as e:
            if self.logger:
                # get the index of -satsys and retrieve the value of the following value
                # this is the GNSS system that gfzrnx failed to process
                idx_satsys = gfzrnx_opts.index("-satsys")
                gnss_list = gfzrnx_opts[idx_satsys + 1]

                self.logger.error(
                    f"{str_red('gfzrnx conversion failed, check availability')} of {str_yellow(gnss_list)} "
                    f"in {str_yellow(self.rnxnav_ifn)}"
                    f"in {str_yellow(self.rnxnav_ifn)}"
                )
                
                result = None
            # raise RuntimeError(
            #     f"{str_red('gfzrnx conversion failed, check availability')} of {str_yellow(gnss_list)} "
            #     f"in {str_yellow(self.rnxnav_ifn)}"
            # )
                
                result = None
            # raise RuntimeError(
            #     f"{str_red('gfzrnx conversion failed, check availability')} of {str_yellow(gnss_list)} "
            #     f"in {str_yellow(self.rnxnav_ifn)}"
            # )
        except PermissionError as e:
            if self.logger:
                self.logger.error(
                    f"{str_red('Permission error running gfzrnx')}: {str(e)}"
                )
            raise PermissionError(
                f"{str_red('Permission error running gfzrnx')}: {str(e)}"
            )

        # check if selected GNSS has data in result.stdout
        if result is  None:
            return
        

        # check if selected GNSS has data in result.stdout
        if result is  None:
            return
        
        # read the first line of the output to get initial part of column names
        hdr_line = result.stdout.split("\n")[0]

        # Read into DataFrame skipping the first line
        df_all_nav = pl.read_csv(
            StringIO(result.stdout), has_header=False, separator=",", skip_rows=1
        )
        #     self.logger.debug(
        #         f"Converted RINEX navigation file to tabular navigation file for "
        #         f"{str_green(', '.join([GNSS_DICT[gnss] for gnss in self.gnss]))}: \n"
        #         f"{df_all_nav}"
        #     )

        # Group by GNSS type (column_2) and navigation type (column_7) and create
        # dictionary of DataFrames, key of dataframe is the tuple (gnss_type, nav_type)
        nav_dict = {
            (gnss_type, nav_type): group_df
            for (gnss_type, nav_type), group_df in df_all_nav.group_by(
                ["column_2", "column_7"], maintain_order=True
            )
        }

        # obtained tabular navigation files for selected GNSS systems, process each GNSS sub-DataFrame
        for (gnss, nav_type), tabnav_df in nav_dict.items():
            # if self.logger is not None:
            #         self.logger.debug(
            #             f"Correcting headers of navigation dataframe for "
            #             f"{str_green(GNSS_DICT[gnss])} - {str_green(nav_type)}: \n"
            #             f"{tabnav_df}"
            #         )
            # set correct columns names to each DataFrame
            colnames_hdr = hdr_line.split(",DATA")[0].split(",")
            colnames_nav = rcn.get_nav_param_names(gnss, nav_type).split(",")
            new_columns = colnames_hdr + colnames_nav

            # rename the columns of the DataFrame
            tabnav_df.columns = new_columns

            # Convert columns with null-safe approach
            columns_to_convert = {
                "TIME": (pl.col("TIME").cast(pl.Int64, strict=False)),
                "tk": (pl.col("tk").cast(pl.Int64, strict=False)),
                "health": (pl.col("health").cast(pl.Int64, strict=False)),
                "freqNum": (pl.col("freqNum").cast(pl.Int16, strict=False)),
                "age": (pl.col("age").cast(pl.Int32, strict=False)),
                "TauN": (pl.col("TauN").str.strip().cast(pl.Float64, strict=False)),
            }

            for col, col_format in columns_to_convert.items():
                if col in tabnav_df.columns:
                    tabnav_df = tabnav_df.with_columns(col_format)

            # remove duplicate rows from tabnav_df
            tabnav_df = tabnav_df.unique()
            self.logger.debug(f"tabnav_df = \n{tabnav_df}")

            # adjust the DATE/TIME to get WKNR and TOW columns
            tabnav_df = (
                tabnav_df.with_columns(
                    [
                        (pl.col("DATE") // 10).alias("WKNR"),
                        (pl.col("DATE") % 10 * 86400 + pl.col("TIME")).alias("TOW"),
                        (
                            pl.col("PRN")
                            .str.extract(r"(\d+)")
                            .cast(pl.Int16)
                            .alias("PRN")
                        ),
                    ]
                )
                .filter(pl.col("TOW").is_not_null())  # Remove rows where TOW is null
                .drop(["DATE", "TIME", "#HD", "NAV"])
                .select(["WKNR", "TOW", pl.all().exclude(["WKNR", "TOW"])])
            )

            # sent to logger
            if self.logger is not None:
                self.logger.debug(
                    f"tabnav_df[{str_green(DICT_GNSS[gnss]["name"])}, {str_green(nav_type)}] = \n{tabnav_df}"
                )

            # replace the tabnav_df on nav_dict after having renamed the columns
            nav_dict[(gnss, nav_type)] = tabnav_df

        # return the dictionary of DataFrames with keys of tuples (gnss, nav_type)
        return nav_dict
