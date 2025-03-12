# Standard library imports
import datetime
import glob
import logging
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field

# Third-party imports
import numpy as np
import polars as pl
import utm
from rich import print as rprint

from analysegnss.config import ERROR_CODES, rich_console
from analysegnss.gnss.gnss_dt import gpsms2dt
from analysegnss.sbf import sbf_constants as sbfc
from analysegnss.sbf.sbf_blocks_polars import (
    SBF_BLOCK_COLUMNS_BIN2ASC,
    SBF_BLOCK_COLUMNS_SBF2ASC,
)
from analysegnss.utils.utilities import locate, str_red, str_yellow


@dataclass
class SBF:
    sbf_fn: str = field(default=None)
    start_time: datetime.time = field(default=None)
    end_time: datetime.time = field(default=None)

    logger: logging.Logger = field(default=None)
    _console_loglevel: int = field(default=logging.ERROR)

    def __post_init__(self):
        self.validate_file()
        self.validate_start_time()
        self.validate_end_time()
        self.validate_logger_level()

    def validate_file(self):
        if not os.path.isfile(self.sbf_fn):
            if self.logger:
                self.logger.error(f"File does not exist: {self.sbf_fn}")
            raise ValueError(f"File does not exist: {self.sbf_fn}")

        # TODO The following sometimes gives a false negative. Needs to be revised.
        with open(self.sbf_fn, "rb") as f:
            first_two_bytes = f.read(2)

        if first_two_bytes != b"$@":
            if self.logger:
                self.logger.error(
                    f'Invalid file type, first two bytes must be "$@" for file: {self.sbf_fn}'
                )
        """
			raise ValueError(
				f'File type is not valid, first two bytes must be "$@": {self.sbf_fn}'
			)
		"""

        if self.logger:
            self.logger.debug(f"File validated successfully: {self.sbf_fn}")

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
                    self.logger.debug(
                        f"Start time {self.start_time} validated successfully."
                    )
        else:
            if self.logger:
                self.logger.debug("No start time specified.")

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
                    self.logger.debug(
                        f"end time {self.end_time} validated successfully."
                    )
        else:
            if self.logger:
                self.logger.debug("No end time specified.")

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

            self.logger.debug(
                "Console log level set to "
                + f"{str_red(logging.getLevelName(self._console_loglevel))}"
            )

    def archive_file(self, fn: str, dest_dir: str):
        """
        archive_file archives the created ascii files.
        It copies the source to the archiving destination and adds a timestamp.

        args:
        fn: file name to archive
        dest_dir: name of archive directory

        """
        # Getting directory of file to archive
        dir_fn = os.path.dirname(fn)
        dir_archive_ofn = os.path.join(dir_fn, dest_dir)
        self.logger.debug(f"archive directory of file is {dir_archive_ofn}")

        # create directory if it does not exist
        if not os.path.exists(dir_archive_ofn):
            try:
                os.makedirs(dir_archive_ofn, exist_ok=True)
                self.logger.info(f"Directory {dir_archive_ofn} created.")
            except Exception as e:
                self.logger.error(
                    f"Error creating archive directory {dir_archive_ofn}: {e}"
                )

        # extract base name
        fn_base = os.path.basename(fn)

        # Get timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        fn_time = timestamp + "_" + fn_base

        # update destination
        dest = os.path.join(dir_archive_ofn, fn_time)

        # copy file to archive directory
        try:
            shutil.copy2(fn, dest)
            self.logger.info(f"Successfully archived file {fn} to {dest}")

        except Exception as e:
            self.logger.error(
                f"Error moving file {fn} to archive directory {dest}: {e}"
            )

    def get_sbf_blocks(self) -> list:
        """
        get_sbf_blocks returns a list of SBF blocks from the SBF file
        """

        def clean_block_name(text):
            # Remove " (v1)"
            text = text.replace(" (v1)", "")
            # Convert " (v2)" to "2"
            text = text.replace(" (v2)", "2")
            return text

        # sbf to CSV conversion utility
        run_sbfblocks = locate("sbfblocks")
        # options for sbfblocks
        cmd_sbfblocks = [run_sbfblocks, "-f", self.sbf_fn, "-E"]

        # run sbfblocks command
        with rich_console.status(
            f"[bold green]getting list of SBF blocks in {self.sbf_fn}",
            spinner="aesthetic",
        ):
            try:
                process = subprocess.run(cmd_sbfblocks)
            except Exception as e:
                sys.stderr.write(f"{process} Error: {e}\n")
                if self.logger:
                    self.logger.error(
                        f"\t... subprocess {str_yellow(' '.join(cmd_sbfblocks))} return exit code"
                        f"\t... {str_red(e)}. Program exits."
                    )
                sys.exit(ERROR_CODES["E_PROCESS"])

        # read the output of sbfblocks
        sbfblocks_ifn = self.sbf_fn + ".blocks.txt"
        with open(sbfblocks_ifn, "r") as f:
            lines = f.readlines()

        extracted_sbfblocks = []
        for line in lines:
            # Find text between "] " and " ="
            start = line.find("] ") + len("] ")
            end = line.find(" =")
            if end != -1:
                field = line[start:end]
                extracted_sbfblocks.append(clean_block_name(text=field))

        return extracted_sbfblocks

    def bin2asc_dataframe(self, lst_sbfblocks: list, archive=None) -> dict:
        """
        bin2asc_dataframe converts binary SBF to CVS files for the sbfblocks in
        lst_sbfblocks and load these files in dataframes

        Arguments:
                lst_sbfblocks: list of SBF blocks to convert to a dataframe
                (Remark; sbfblocks starting with Meas3... are not decoded using bin2asc)

        Raises:
                Exception when the bin2asc program fails

        Returns:
                dict of sbfblocks and corresponding dataframes
        """
        # sbf to CSV conversion utility
        run_bin2asc = locate("bin2asc")
        if self.logger:
            self.logger.info(
                f"{str_yellow(run_bin2asc)} conversion of SBF file {str_yellow(self.sbf_fn)} to CSV files\n"
                f"Importing into dataframes for SBF blocks: {str_yellow(' '.join(lst_sbfblocks))}"
            )

        # create options for bin2asc
        cmd_bin2asc = [
            run_bin2asc,
            "-f",
            self.sbf_fn,
            "-n",
            "NaN",
            "-E",
            "-r",
            "-t",
        ]

        if self.start_time is not None:
            cmd_bin2asc.append("-b")
            cmd_bin2asc.append(self.start_time.strftime("%H:%M:%S"))
        if self.end_time is not None:
            cmd_bin2asc.append("-e")
            cmd_bin2asc.append(self.end_time.strftime("%H:%M:%S"))

        # # add logging level to cmd_bin2asc when self._console_loglevel is DEBUG
        # if self._console_loglevel == logging.DEBUG:
        #     cmd_bin2asc.append("-v")

        for sbf_block in lst_sbfblocks:
            cmd_bin2asc.append("-m")
            cmd_bin2asc.append(sbf_block)
            if sbf_block == "Meas3Ranges":
                cmd_bin2asc.append("--extractGenMeas")

        # Convert binary to text messages
        if self.logger:
            self.logger.debug(f"... running: {str_yellow(' '.join(cmd_bin2asc))}")

        with rich_console.status(
            f"Converting SBF blocks [bold green]({lst_sbfblocks})[/bold green] to CSV files running:\n"
            f"\t{' '.join(cmd_bin2asc)}\n",
            spinner="aesthetic",
        ):
            try:
                process = subprocess.run(cmd_bin2asc)
            except Exception as e:
                sys.stderr.write(f"{process} Error: {e}\n")
                if self.logger:
                    self.logger.error(
                        f"\t... subprocess {str_yellow(' '.join(cmd_bin2asc))} return exit code"
                        f"\t... {str_red(e)}. Program exits."
                    )
                sys.exit(ERROR_CODES["E_PROCESS"])

        # find created files
        bin2asc_fns = {}
        for sbf_block in lst_sbfblocks:
            if sbf_block != "Meas3Ranges":
                bin2asc_fns[sbf_block] = glob.glob(
                    rf"{self.sbf_fn}_SBF_{sbf_block}.txt"
                )[0]
            else:
                bin2asc_fns[sbf_block] = glob.glob(rf"{self.sbf_fn}_measurements.txt")[
                    0
                ]

        # create dictionary for containing the obtained dataframes
        sbf_dfs = {}

        # iterate over the CVS files and convert them to dataframe
        for sbf_block, bin2asc_fn in bin2asc_fns.items():
            # check if bin2asc_fn of sbf block is empty
            if len(bin2asc_fn) == 0:
                if self.logger:
                    self.logger.warning(
                        f"\t... no file for {str_yellow({sbf_block})} sbf block found. "
                        f"Continuing to next sbf block."
                    )
            else:
                if self.logger:
                    self.logger.debug(
                        f"\t... converting {str_yellow(bin2asc_fn)} to dataframe"
                    )

                # remove unused columns
                keep_cols = self.used_columns(sbf_block)
                print(f"\ninital keep_cols = {keep_cols}\n")

                # read csv file into dataframe
                with rich_console.status(
                    f"Reading from CSV file [bold green]{sbf_block}[/bold green]\n",
                    spinner="aesthetic",
                ):
                    sbf_df = pl.read_csv(
                        source=bin2asc_fn,
                        separator=",",
                        # columns=original_cols,
                        # new_columns=original_cols,  # This preserves exact column names
                        comment_prefix="#",
                        has_header=True,
                        skip_rows_after_header=1,  # Skip 1 row after the header
                        # dtypes=keep_cols,
                        null_values=[
                            "null",
                            "NaN",
                        ],  # First catch all null representations
                    ).fill_null(
                        float("nan")
                    )  # Then convert all nulls to NaN

                with rich_console.status(
                    f"Adjusting columns for [bold green]{sbf_block}[/bold green]\n",
                    spinner="aesthetic",
                ):
                    # add columns to the dataframe
                    sbf_df, added_cols, removed_cols = self.add_columns(block_df=sbf_df)
                    # adjust the keep_cols adding and removing the columns
                    for col_name, col_dtype in added_cols.items():
                        keep_cols[col_name] = col_dtype
                    for col_name in removed_cols:
                        del keep_cols[col_name]
                    print(f"\nupdated keep_cols = {keep_cols}\n")

                    # print(
                    #     f"sbf_df[{sbf_block}]:\n{sbf_df.select(sbf_df.columns[:20]).head(3)}"
                    #     f"sbf_df[{sbf_block}]:\n{sbf_df.select(sbf_df.columns[20:]).head(3)}"
                    # )

                    # # we changed some values (eg. from rad to deg) so rename the columns
                    # # Get keys that need to be changed
                    # keys_to_change = [
                    #     key
                    #     for key in keep_cols.keys()
                    #     if "rad" in key and ("Latitude" in key or "Longitude" in key)
                    # ]

                    # # Update each key
                    # for old_key in keys_to_change:
                    #     value = keep_cols[old_key]
                    #     new_key = old_key.replace("rad", "deg")
                    #     new_key = new_key.replace("Latitude", "latitude").replace(
                    #         "Longitude", "longitude"
                    #     )
                    #     keep_cols[new_key] = value
                    #     del keep_cols[old_key]

                    # print the column names of sbf_df one per line
                    # for col_name in sbf_df.columns:
                    #     print(col_name)
                    print(f"sbf_df.columns = {sbf_df.columns}")

                    # set the dtype again after having added some columns
                    # identify columns with null values and applies different strategies based on the target data type
                    cast_expressions = []
                    for col_name, dtype in keep_cols.items():
                        # For integer types, check if we need to handle nulls
                        if str(dtype).startswith(("UInt", "Int")):
                            # For columns that might have nulls, first fill nulls with a default value
                            # rprint(
                            #     f"col_name = {col_name}\n{sbf_df[col_name]}\n{sbf_df[col_name].null_count()}"
                            # )
                            if sbf_df[col_name].null_count() > 0:
                                cast_expressions.append(
                                    pl.col(col_name)
                                    .fill_null(0)
                                    .cast(dtype)
                                    .alias(col_name)
                                )
                            else:
                                cast_expressions.append(pl.col(col_name).cast(dtype))
                        else:
                            # For other types, just perform the regular cast
                            cast_expressions.append(pl.col(col_name).cast(dtype))

                    sbf_df = sbf_df.with_columns(cast_expressions)

                    # TODO: AMAMAMAMcheck the columns in the dataframe to see whether we only keep the keep_columns????
                    print("=" * 60)
                    print(f"sbf_block = {sbf_block}")
                    print(f"sbf_df.columns = {sbf_df.columns} | {len(sbf_df.columns)}")
                    print(
                        f"\nkeep_cols.keys() = {keep_cols.keys()} | {len(keep_cols.keys())}"
                    )
                    print("-" * 60)

                    # drop the columns which are not in the keep_cols
                    for col_name in sbf_df.columns:
                        if col_name not in keep_cols.keys():
                            sbf_df = sbf_df.drop(col_name)
                    print("+" * 60)
                    print(f"sbf_block = {sbf_block}")
                    print(f"sbf_df.columns = {sbf_df.columns} | {len(sbf_df.columns)}")
                    print(
                        f"\nkeep_cols.keys() = {keep_cols.keys()} | {len(keep_cols.keys())}"
                    )
                    print("#" * 60)

                    print(f"sbf_df[{sbf_block}]:\n{sbf_df}")
                    if len(sbf_df.columns) > 15:
                        print(
                            f"\n\ndf_pvt[{sbf_block}]:\n{sbf_df.select(sbf_df.columns[:15]).head(3)}"
                            f"\n{sbf_df.select(sbf_df.columns[15:]).head(3)}\n\n"
                        )
                    else:
                        print(
                            f"\n\ndf_pvt[{sbf_block}]:\n{sbf_df.select(sbf_df.columns).head(3)}\n\n"
                        )

                sbf_dfs[sbf_block] = sbf_df
                # print(f"sbf_dfs[{sbf_block}]:\n{sbf_dfs[sbf_block]}")

                # print(f"archive = {archive}")
                # archiving the converted sbf file
                if not archive == None:
                    self.archive_file(fn=bin2asc_fn, dest_dir=archive)

        if sbf_dfs == {}:
            if self.logger:
                self.logger.error(
                    f"\t... Unable to create dataframes for the provided SBF blocks {str_yellow(lst_sbfblocks)} found. Exiting."
                )
            sys.exit(ERROR_CODES["E_PROCESS"])

        return sbf_dfs

    def sbf2asc_dataframe(self, lst_sbfblocks: list, archive=None) -> dict:
        """
        this definition is analogue to bin2asc and is used to convert the SBF files to dataframes.
        Sbf2asc can be installed on most platforms including OS running on ARM processors (e.g. Raspberry Pi).
        This is not the case for bin2asc

        Arguments:
                lst_sbfblocks: list of SBF blocks to convert to a dataframe
                (Remark; sbfblocks starting with Meas3... are not decoded using bin2asc)

        Raises:
                Exception when the bin2asc program fails

        Returns:
                dict of sbfblocks and corresponding dataframes
        """
        # sbf to CSV conversion utility
        run_sbf2asc = locate("sbf2asc")
        if run_sbf2asc is None:
            self.logger.error(
                f"sbf2asc not found in PATH. Please install sbf2asc. Program exits."
            )
            sys.exit(ERROR_CODES["E_PROCESS"])

        if self.logger:
            self.logger.info(
                f"{str_yellow(run_sbf2asc)} conversion of SBF file {str_yellow(self.sbf_fn)} to CSV files "
                f"and importing into dataframes for SBF blocks\n{str_yellow(' '.join(lst_sbfblocks))}"
            )

        # create options for sbf2asc
        cmd_sbf2asc = [
            run_sbf2asc,
            "-f",
            self.sbf_fn,
            "-E",
            "-o",
        ]

        for sbf_block in lst_sbfblocks:
            cmd_sbf2asc.append(
                f"{self.sbf_fn}_sbf2asc_{sbf_block}.txt"
            )  # this comes after the -o argument so a correct output file is created
            sbf2asc_block = self.sbf2asc_convert_sbfblock(sbf_block=sbf_block)
            cmd_sbf2asc.append(sbf2asc_block)

        # add logging level to cmd_sbf2asc when self._console_loglevel is DEBUG
        if self._console_loglevel == logging.DEBUG:
            cmd_sbf2asc.append("-v")

        # Convert binary to text messages
        if self.logger:
            self.logger.debug(f"... running: {str_yellow(' '.join(cmd_sbf2asc))}")

        try:
            process = subprocess.run(cmd_sbf2asc)
        except Exception as e:
            sys.stderr.write(f"{process} Error: {e}\n")
            self.logger.error(
                f"\t... subprocess {str_yellow(' '.join(cmd_sbf2asc))} return exit code"
                f"\t... {str_red(e)}. Program exits."
            )
            sys.exit(ERROR_CODES["E_PROCESS"])

        # find created files
        sbf2asc_fns = {}
        for sbf_block in lst_sbfblocks:
            sbf2asc_fns[sbf_block] = glob.glob(
                rf"{self.sbf_fn}_sbf2asc_{sbf_block}.txt"
            )

        # create dictionary for containing the obtained dataframes
        sbf_dfs = {}

        # iterate over the CVS files and convert them to dataframe
        for sbf_block, sbf2asc_fn in sbf2asc_fns.items():
            # check if bin2asc_fn of sbf block is empty
            if len(sbf2asc_fn) == 0:
                if self.logger:
                    self.logger.warning(
                        f"\t... no file for {str_yellow({sbf_block})} sbf block found. Continuing to next sbf block."
                    )
            else:
                if self.logger:
                    self.logger.debug(
                        f"\t... converting {str_yellow(sbf2asc_fn[0])} to dataframe"
                    )

            # REMOVING WHITESPACES from the file content
            # sed_cmd = r"sed 's/[[:blank:]]\{1,\}/,/g'"
            # sed_cmd = sed_cmd + f" {sbf2asc_fn[0]}"
            # # print(f"sed_cmd = {sed_cmd}")
            # content = os.popen(sed_cmd).read()
            # with open(sbf2asc_fn[0], "w") as fd:
            #     fd.write(content)

            with open(sbf2asc_fn[0], "r") as f:
                lines = []
                for line in f:
                    processed_line = ",".join(line.split())
                    lines.append(processed_line)
                content = "\n".join(lines)

            with open(sbf2asc_fn[0], "w") as fd:
                fd.write(content)
            # remove unused columns
            sbf_df = pl.DataFrame()

            try:
                sbf_df = pl.read_csv(
                    source=sbf2asc_fn[0],
                    has_header=False,
                    separator=",",
                    new_columns=self.sbf2asc_sbfblock_colnames(sbf_block=sbf_block),
                )
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error reading file {sbf2asc_fn[0]}: {e}")
            except pl.exceptions.NoDataError as e:
                if self.logger:
                    self.logger.error(f"Empty file {sbf2asc_fn[0]}: {e}")

            # Drop columns with only zeroes
            sbf_df = sbf_df.drop(
                columns=[col for col in sbf_df.columns if sbf_df[col].sum() == 0]
            )

            # TODO add columns to the dataframe of sbf2asc e.g. time, ...etc
            # sbf_df = self.add_columns(block_df=sbf_df)

            sbf_dfs[sbf_block] = sbf_df

            if self.logger:
                self.logger.info(f"successfully created  dataframe for {sbf_block}")
                self.logger.info(sbf_dfs[sbf_block])
                if not archive == None:
                    # Archive the created files
                    self.archive_file(fn=sbf2asc_fn[0], dest_dir=archive)

        if sbf_dfs == {}:
            if self.logger:
                self.logger.error(
                    f"\t... Unable to create dataframes for the provided SBF blocks {str_yellow(lst_sbfblocks)} found. Exiting."
                )
            sys.exit(ERROR_CODES["E_PROCESS"])

        return sbf_dfs

    def add_columns(self, block_df: pl.DataFrame) -> tuple[pl.DataFrame, dict, list]:
        """checks if we can create a datetime,PRN, UTM columns in the dataframe

        Args:
                block_df (pl.DataFrame): dataframe corresponding to a SBF block

        Returns:
                pl.DataFrame: dataframe with datetime and PRN columns added if possible
                dict: columns added with dtype
                list: columns removed with dtype
        """
        # adding/removing columns based on information available, so keep track of those columns and dtypes
        added_cols = {}
        removed_cols = []

        # remove the rows where 'Type' equals 0 (no PVT available)
        if "Type" in block_df.columns:
            block_df = block_df.filter(pl.col("Type") != 0).lazy()
            # print(f"block_df = \n{block_df}")

        # add date-time and PRN (as str) to the dataframe
        if "WNc [w]" in block_df.columns and "TOW [0.001 s]" in block_df.columns:
            if self.logger:
                self.logger.debug("\tadding datetime column to the dataframe")
            block_df = block_df.with_columns(
                pl.struct(["WNc [w]", "TOW [0.001 s]"])
                .map_elements(
                    lambda x: gpsms2dt(week=x["WNc [w]"], towms=x["TOW [0.001 s]"]),
                    return_dtype=pl.Datetime,
                )
                .alias("DT")
            ).lazy()
            added_cols["DT"] = pl.Datetime

        # add date-time and PRN (as str) to the dataframe
        if "WNc [w]" in block_df.columns and "TOW [s]" in block_df.columns:
            if self.logger:
                self.logger.debug("\tadding datetime column to the dataframe")
            block_df = block_df.with_columns(
                pl.struct(["WNc [w]", "TOW [s]"])
                .map_elements(
                    lambda x: gpsms2dt(week=x["WNc [w]"], towms=x["TOW [s]"]),
                    return_dtype=pl.Datetime,
                )
                .alias("DT")
            ).lazy()
            added_cols["DT"] = pl.Datetime

        # add date-time and PRN (as str) to the dataframe
        if (
            "SVID"
            in block_df.columns
            # and not block_df.select(pl.col("SVID")).dtypes[0] == pl.String
        ):
            if self.logger:
                self.logger.debug("\tadding PRN column to the dataframe")
            block_df = block_df.with_columns(
                pl.struct(["SVID"])
                .map_elements(
                    lambda x: sbfc.ssnerr_prn2str(prn=x["SVID"]),
                    return_dtype=pl.Utf8,
                )
                .alias("PRN")
            ).lazy()
            block_df = block_df.drop(["SVID"]).lazy()
            added_cols["PRN"] = pl.Utf8
            removed_cols.append("SVID")

        # add UTM coordinates
        if (
            "Latitude [rad]" in block_df.columns
            and "Longitude [rad]" in block_df.columns
        ):
            if self.logger:
                self.logger.debug("\tadding UTM coordinates to the dataframe")

            # Function to convert lat/lon in degrees to UTM
            def latlon_to_utm(lat, lon):
                easting, northing, _, _ = utm.from_latlon(lat, lon)
                return {"easting": easting, "northing": northing}

            # Convert latitude and longitude from radians to degrees
            block_df = block_df.with_columns(
                [
                    (pl.col("Latitude [rad]") * 180 / np.pi).alias("latitude [deg]"),
                    (pl.col("Longitude [rad]") * 180 / np.pi).alias("longitude [deg]"),
                ]
            ).lazy()

            # Apply the conversion function lazily using map_elements with specified return_dtype
            block_df = block_df.with_columns(
                [
                    pl.struct(["latitude [deg]", "longitude [deg]"])
                    .map_elements(
                        lambda row: latlon_to_utm(
                            row["latitude [deg]"], row["longitude [deg]"]
                        ),
                        return_dtype=pl.Struct(
                            [
                                pl.Field("easting", pl.Float64),
                                pl.Field("northing", pl.Float64),
                            ]
                        ),
                    )
                    .alias("utm_coords")
                ]
            ).lazy()

            # Extract the UTM.East and UTM.North from the computed struct
            block_df = block_df.with_columns(
                [
                    pl.col("utm_coords").struct.field("easting").alias("UTM.E"),
                    pl.col("utm_coords").struct.field("northing").alias("UTM.N"),
                ]
            ).lazy()

            # Drop intermediate columns
            block_df = block_df.drop(
                ["Latitude [rad]", "Longitude [rad]", "utm_coords"]
            ).lazy()
            added_cols["latitude [deg]"] = pl.Float64
            added_cols["longitude [deg]"] = pl.Float64
            added_cols["UTM.E"] = pl.Float64
            added_cols["UTM.N"] = pl.Float64
            removed_cols.extend(["Latitude [rad]", "Longitude [rad]"])

        # add orthometric height to the dataframe
        if "Height [m]" in block_df.columns and "Undulation [m]" in block_df.columns:
            if self.logger:
                self.logger.debug("\tadding orthometric height to the dataframe")
            block_df = block_df.with_columns(
                pl.struct(["Height [m]", "Undulation [m]"])
                .map_elements(
                    lambda x: x["Height [m]"] - x["Undulation [m]"],
                    return_dtype=pl.Float64,
                )
                .alias("orthoH")
            ).lazy()
            added_cols["orthoH"] = pl.Float64

        # If an SBF block doesn't contain a column used in this func,
        # the collect() will throw an error.
        if getattr(block_df, "collect", None) is not None:
            block_df = block_df.collect()

        return block_df, added_cols, removed_cols

    def used_columns(self, sbf_block: str) -> list:
        """returns the column names and dtype we use when extracting a SBF block from the SBF file

        Args:
                sbf_block (str): the SBF block we are extracting

        Returns:
                list: column names we use with dtype
        """
        if sbf_block not in SBF_BLOCK_COLUMNS_BIN2ASC.keys():
            if self.logger:
                self.logger.error(f"Unknown SBF block type: {sbf_block}")
            return {}

        col_types = SBF_BLOCK_COLUMNS_BIN2ASC[sbf_block]
        keep_cols = {}

        for dtype, columns in col_types.items():
            for col in columns:
                keep_cols[col] = dtype

        if self.logger is not None:
            self.logger.debug(f"Keeping columns: \n{keep_cols}")

        return keep_cols

    def convert_Cov2SD(self, df_cov: pl.DataFrame) -> pl.DataFrame:
        """Convert covariance matrix to standard deviation

        Args:
                df_cov (pl.DataFrame): df with covariance diagonal elements

        Returns:
                pl.DataFrame: df with standard deviations
        """
        # Define column name mapping
        rename_map = {
            "Cov_latlat [m²]": "SD_lat [m]",
            "Cov_lonlon [m²]": "SD_lon [m]",
            "Cov_hgthgt [m²]": "SD_hgt [m]",
            "Cov_bb [m²]": "SD_bb [m]",
        }

        return (
            df_cov.lazy()
            .with_columns(
                [
                    (pl.col(col) ** 0.5).alias(rename_map.get(col, col))
                    for col in rename_map.keys()
                ]
            )
            .drop(rename_map.keys())
            # .drop(["TOW [0.001 s]", "WNc [w]"])
            .collect()
        )

    def sbf2asc_convert_sbfblock(self, sbf_block: str) -> str:
        """This looks up which sbf2asc argument belongs to which sbfblock

        Arguments:
                lst_sbfblocks: list of SBF blocks to convert to a dataframe

        Returns:
                str of correspond sbfblock argument for sbf2asc cli program
        """

        if self.logger is not None:
            self.logger.info(
                "sbf2asc is chosen as sbf converter. Looking up corresponding sbf block arguments"
            )

        # TODO expand look up table for sbf2asc
        lookup_sbf_block = {
            "PVTCartesian2": "-p",
            "PVTGeodetic2": "-g",
            "PosCovCartesian1": "-c",
        }

        try:
            sbf_block_sbf2asc = lookup_sbf_block[sbf_block]
            self.logger.info(
                f"Returning sbf block {sbf_block} corresponding arguments {sbf_block_sbf2asc} for sbf2asc"
            )
        except KeyError as e:
            self.logger.error(f"Could not find sbf block {sbf_block} in lookup table")
            sys.exit(ERROR_CODES["E_NO_SBF_BLOCK"])

        return sbf_block_sbf2asc

    def sbf2asc_sbfblock_colnames(self, sbf_block: str) -> list:
        """The sbf2asc does not give any header information.
        This function looks up the column names for each sbf block

        Arguments:
                lst_sbfblocks: list of SBF blocks to convert to a dataframe

        Raises:
                Exception when the sbf2asc program fails

        Returns:
                list of correct column names for each sbfblocks
        """
        print(
            "sbf2asc is chosen as sbf converter. Looking up corresponding column names for each sbf block"
        )
        self.logger.info(
            "sbf2asc is chosen as sbf converter. Looking up corresponding column names for each sbf block"
        )

        try:
            sbf_block_colnames = SBF_BLOCK_COLUMNS_SBF2ASC[sbf_block]
            if self.logger:
                self.logger.info(
                    f"Returning sbf block {sbf_block} corresponding column names {sbf_block_colnames} for sbf2asc"
                )
        except KeyError as e:
            if self.logger:
                self.logger.error(
                    f"Could not find sbf block {sbf_block} in lookup table"
                )

            sys.exit(ERROR_CODES["E_NO_SBF_BLOCK"])

        return sbf_block_colnames
