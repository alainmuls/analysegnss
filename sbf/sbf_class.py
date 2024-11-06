import datetime
import glob
import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field

import numpy as np
import polars as pl
import utm

from config import ERROR_CODES
from gnss.gnss_dt import gpsms2dt
from sbf import sbf_constants as sbfc
from utils.utilities import locate, str_red, str_yellow


@dataclass
class SBF:
    sbf_fn: str
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

        with open(self.sbf_fn, "rb") as f:
            first_two_bytes = f.read(2)

        if first_two_bytes != b"$@":
            if self.logger:
                self.logger.error(
                    f'Invalid file type, first two bytes must be "$@" for file: {self.sbf_fn}'
                )
            raise ValueError(
                f'File type is not valid, first two bytes must be "$@": {self.sbf_fn}'
            )

        if self.logger:
            self.logger.info(f"File validated successfully: {self.sbf_fn}")

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

    def bin2asc_dataframe(self, lst_sbfblocks: list) -> dict:
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
                f"{str_yellow(run_bin2asc)} conversion of SBF file {str_yellow(self.sbf_fn)} to CSV files "
                f"and importing into dataframes for SBF blocks\n{str_yellow(' '.join(lst_sbfblocks))}"
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
        # "-b",
        # self.epoch_start.strftime("%H:%M:%S"),
        # "-e",
        # self.epoch_end.strftime("%H:%M:%S"),

        # add logging level to cmd_bin2asc when self._console_loglevel is DEBUG
        if self._console_loglevel == logging.DEBUG:
            cmd_bin2asc.append("-v")

        for sbf_block in lst_sbfblocks:
            cmd_bin2asc.append("-m")
            cmd_bin2asc.append(sbf_block)

        # Convert binary to text messages
        if self.logger:
            self.logger.debug(f"... running: {str_yellow(' '.join(cmd_bin2asc))}")

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
            bin2asc_fns[sbf_block] = glob.glob(rf"{self.sbf_fn}_SBF_{sbf_block}.txt")

        # create dictionary for containing the obtained dataframes
        sbf_dfs = {}

        # iterate over the CVS files and convert them to dataframe
        for sbf_block, bin2asc_fn in bin2asc_fns.items():
            if self.logger:
                self.logger.debug(
                    f"\t... converting {str_yellow(bin2asc_fn[0])} to dataframe"
                )

            # remove unused columns
            keep_cols = self.used_columns(sbf_block)
            # print(f"list(keep_cols.keys()) = \n{list(keep_cols.keys())}")

            sbf_df = pl.read_csv(
                source=bin2asc_fn[0],
                separator=",",
                columns=list(keep_cols.keys()),
                comment_prefix="#",
                has_header=True,
                skip_rows_after_header=1,  # Skip 1 row after the header
                dtypes=keep_cols,
                null_values="NaN",
            )

            # add columns to the dataframe
            sbf_df = self.add_columns(block_df=sbf_df)

            sbf_dfs[sbf_block] = sbf_df

        return sbf_dfs

    def sbf2asc_dataframe(self, lst_sbfblocks: list) -> dict:
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
        run_sbf2asc = "/home/base/Programs_BaseStation/sbf2asc/sbf2asc"
        if self.logger:
            self.logger.info(
                f"{str_yellow(run_sbf2asc)} conversion of SBF file {str_yellow(self.sbf_fn)} to CSV files "
                f"and importing into dataframes for SBF blocks\n{str_yellow(' '.join(lst_sbfblocks))}"
            )

        # create options for bin2asc
        cmd_sbf2asc = [
            run_sbf2asc,
            "-f",
            self.sbf_fn,
            "-E",
            "-o",
        ]

        # add logging level to cmd_bin2asc when self._console_loglevel is DEBUG
        if self._console_loglevel == logging.DEBUG:
            cmd_sbf2asc.append("-v")

        for sbf_block in lst_sbfblocks:
            cmd_sbf2asc.append(
                f"{self.sbf_fn}_sbf2asc_{sbf_block}.txt"
            )  # this comes after the -o argument so a correct output file is created
            sbf2asc_block = self.sbf2asc_convert_sbfblock(sbf_block=sbf_block)
            cmd_sbf2asc.append(sbf2asc_block)

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
                    new_columns=self.sb2asc_sbfblock_colnames(sbf_block=sbf_block),
                )
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error reading file {sbf2asc_fn[0]}: {e}")
            except pl.exceptions.NoDataError as e:
                if self.logger:
                    self.logger.error(f"Empty file {sbf2asc_fn[0]}: {e}")

            # TODO remove unused columns

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

        return sbf_dfs

    def add_columns(self, block_df: pl.DataFrame) -> pl.DataFrame:
        """checks if we can create a datetime,PRN, UTM columns in the dataframe

        Args:
            block_df (pl.DataFrame): dataframe corresponding to a SBF block

        Returns:
            pl.DataFrame: dataframe with datetime and PRN columns added if possible
        """
        # print(f"block_df = \n{block_df}")
        # remove the rows where 'Type' equals 0 (no PVT available)
        if self.logger:
            self.logger.info("\tremoving rows with no PVT solution")

        if "Type" in block_df.columns:
            block_df = block_df.filter(pl.col("Type") != 0).lazy()
            # print(f"block_df = \n{block_df}")

        # add date-time and PRN (as str) to the dataframe
        if "WNc [w]" in block_df.columns and "TOW [0.001 s]" in block_df.columns:
            if self.logger:
                self.logger.info("\tadding datetime column to the dataframe")
            block_df = block_df.with_columns(
                pl.struct(["WNc [w]", "TOW [0.001 s]"])
                .map_elements(
                    lambda x: gpsms2dt(week=x["WNc [w]"], towms=x["TOW [0.001 s]"]),
                    return_dtype=pl.Datetime,
                )
                .alias("DT")
            ).lazy()

        # add date-time and PRN (as str) to the dataframe
        if "SVID" in block_df.columns:
            if self.logger:
                self.logger.info("\tadding PRN column to the dataframe")
            block_df = block_df.with_columns(
                pl.struct(["SVID"])
                .map_elements(
                    lambda x: sbfc.ssnerr_prn2str(prn=x["SVID"]), return_dtype=pl.Utf8
                )
                .alias("PRN")
            ).lazy()

        # add UTM coordinates
        if (
            "Latitude [rad]" in block_df.columns
            and "Longitude [rad]" in block_df.columns
        ):
            if self.logger:
                self.logger.info("\tadding UTM coordinates to the dataframe")

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

        # add orthometric height to the dataframe
        if "Height [m]" in block_df.columns and "Undulation [m]" in block_df.columns:
            if self.logger:
                self.logger.info("\tadding orthometric height to the dataframe")
            block_df = block_df.with_columns(
                pl.struct(["Height [m]", "Undulation [m]"])
                .apply(
                    lambda x: x["Height [m]"] - x["Undulation [m]"],
                    return_dtype=pl.Float64,
                )
                .alias("orthoH")
            ).lazy()

        if self.logger:
            self.logger.warning(f"\tcollecting the dataframe. {str_red('Be patient.')}")

        return block_df.collect()

    def used_columns(self, sbf_block: str) -> list:
        """returns the column names we use when extracting a SBF block from the SBF file

        Args:
            sbf_block (str): the SBF block we are extracting

        Returns:
            list: column names we use
        """
        if sbf_block == "MeasEpoch2":
            keep_cols = [
                "TOW [0.001 s]",
                "WNc [w]",
                "CumClkJumps [0.001 s]",
                "SVID",
                "MeasType",
                "LockTime [s]",
                "SignalType",
                "CN0_dBHz [dB-Hz]",
                "PR_m [m]",
                "Doppler_Hz",
                "L_cycles [cyc]",
            ]
        elif sbf_block == "PVTGeodetic2":
            # ['TOW [0.001 s]', 'WNc [w]', 'Type', 'AutoBase', 'Flag2D', 'Error',
            # 'Latitude [rad]', 'Longitude [rad]', 'Height [m]', 'Undulation',
            # 'Vn [m/s]', 'Ve [m/s]', 'Vu [m/s]', 'COG [°]',
            # 'RxClkBias [ms]', 'RxClkDrift [ppm]', 'TimeSystem', 'Datum',
            # 'NrSV', 'LC', 'FC', 'I', 'AI', 'PA',
            # 'RtkBaseType', 'ReferenceID', 'MeanCorrAge [0.01 s]',
            # 'SignalInfo', 'RAIM integrity flag', 'Integrity failed',
            # 'Storm Flag', 'Accuracy limit exceeded', 'NrBases',
            # 'SeedAge [s]', 'SeedType', 'Latency [0.0001 s]',
            # 'HAccuracy [0.01 m]', 'VAccuracy [0.01 m]', 'Misc',
            # 'Baseline', 'Phase center variation', 'SIGIL',
            # 'RTCMV', 'PPVTAge', 'ARPMarkerOffset']

            # dict of your column names keyed by dtype
            col_types = {
                pl.Float64: [
                    "Latitude [rad]",
                    "Longitude [rad]",
                    "Height [m]",
                ],
                pl.Float32: [
                    "Undulation [m]",
                    "COG [°]",
                ],
                pl.UInt32: [
                    "TOW [0.001 s]",
                    "SignalInfo",
                ],
                pl.UInt16: [
                    "WNc [w]",
                    "MeanCorrAge [0.01 s]",
                ],
                pl.UInt8: [
                    "Type",
                    "Error",
                    "NrSV",
                ],
            }

        elif sbf_block == "PVTCartesian2":
            keep_cols = [
                "TOW [0.001 s]",
                "WNc [w]",
                "Type",
                "Flag2D",
                "Error",
                "X [m]",
                "Y [m]",
                "Z [m]",
                "Undulation [m]",
                "RxClkBias [ms]",
                "RxClkDrift [ppm]",
                "NrSV",
            ]
        elif sbf_block == "PVTResiduals2":
            keep_cols = [
                "TOW [0.001 s]",
                "WNc [w]",
                "N",
                "SVID",
                "FreqNr",
                "Type",
                "MeasInfo",
                "ResidualType",
                "Pseudorange residuals",
                "Carrier-phase residuals",
                "Doppler residuals",
                "Fixed ambiguity",
                "Residual [m]",
                "Residual [cyc]",
                "Residual [m/s]",
            ]
        elif sbf_block == "SatVisibility1":
            keep_cols = [
                "TOW [0.001 s]",
                "WNc [w]",
                "SVID",
                "Azimuth_deg",
                "Elevation_deg",
                "RiseSet",
                "SatelliteInfo",
            ]
        elif sbf_block == "ReceiverTime":
            keep_cols = [
                "TOW [0.001 s]",
                "WNc [w]",
                "UTCYear [Y]",
                "UTCMonth [month]",
                "UTCDay [d]",
                "UTCHour [h]",
                "UTCMin [min.]",
                "UTCSec [s]",
                "DeltaLS [s]",
            ]
        elif sbf_block == "PosCovGeodetic1":
            col_types = {
                pl.Float32: [
                    "Cov_latlat [m²]",
                    "Cov_lonlon [m²]",
                    "Cov_hgthgt [m²]",
                ],
                pl.UInt32: [
                    "TOW [0.001 s]",
                ],
                pl.UInt16: [
                    "WNc [w]",
                ],
            }
        keep_cols = {}
        for dtype, columns in col_types.items():
            for col in columns:
                keep_cols[col] = dtype

        if self.logger is not None:
            self.logger.info(f"Keeping columns: \n{keep_cols}")

        return keep_cols

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
            "PosCovGeodetic1": "-c",
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

    def sb2asc_sbfblock_colnames(self, sbf_block: str) -> list:
        """The sbf2asc does not give any header information.
        This function looks up the column names for each sbf block

        Arguments:
            lst_sbfblocks: list of SBF blocks to convert to a dataframe

        Raises:
            Exception when the sbf2asc program fails

        Returns:
            list of correct column names for each sbfblocks
        """
        ic(
            "sbf2asc is chosen as sbf converter. Looking up corresponding column names for each sbf block"
        )
        self.logger.info(
            "sbf2asc is chosen as sbf converter. Looking up corresponding column names for each sbf block"
        )

        # TODO this dict needs to be expanded
        sbf_blocks_colnames = {
            "PosCovGeodetic1": [
                "-2",
                "Time [GPS seconds]",
                "Cov_XX [m²]",
                "Cov_YY [m²]",
                "Cov_ZZ [m²]",
                "Cov_tt [s²]",
            ]
        }

        try:
            sbf_block_colnames = sbf_blocks_colnames[sbf_block]
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
