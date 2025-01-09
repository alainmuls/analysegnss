import logging
import os
import sys
from dataclasses import dataclass, field

import polars as pl
from rich import print

from analysegnss.config import ERROR_CODES, DICT_GNSS, DICT_SIGNAL_TYPES

from analysegnss.utils.utilities import str_red


@dataclass
class GNSS_CSV:
    csv_fn: str = field(default=None)
    # csv_fns: list = field(default_factory=list)
    # start_time: datetime.time = field(default=None)
    # end_time: datetime.time = field(default=None)
    GNSS: str = field(default="G")
    interval: float = field(default=10.0)
    signal_type: str = field(default="1C")

    logger: logging.Logger = field(default=None)
    _console_loglevel: int = field(default=logging.ERROR)
    _gnss_name: str = field(default=None)

    def __post_init__(self):
        self.validate_file()
        # self.validate_start_time()
        # self.validate_end_time()
        self.validate_gnss()
        self.validate_interval()
        self.validate_signal_type()
        self.validate_logger_level()

    def validate_file(self):
        """Validate existence and readability of CSV file

        Raises:
            ValueError: when file doesn't exist or isn't readable
        """
        # Check if file exists and is readable
        if not os.path.isfile(self.csv_fn) or not os.access(self.csv_fn, os.R_OK):
            if self.logger:
                self.logger.error(
                    f"File does not exist or is not readable: {str_red(self.csv_fn)}"
                )
            raise ValueError(
                f"File does not exist or is not readable: {str_red(self.csv_fn)}"
            )

    # def validate_start_time(self):
    #     """
    #     Validates the `start_time` attribute of the `GLABNG` class.
    #     If `start_time` is not `None`, it checks if it is a valid `datetime.time` object.
    #     If it is not valid, it logs an error message and raises a `ValueError`.
    #     If `start_time` is valid, it logs an informational message.
    #     If `start_time` is `None`, it logs an informational message.
    #     """
    #     if self.start_time is not None:
    #         if not isinstance(self.start_time, datetime.time):
    #             if self.logger:
    #                 self.logger.error(
    #                     f"Invalid start_time {self.start_time}: not a valid datetime.time object."
    #                 )
    #             raise ValueError(
    #                 f"Invalid start_time {self.start_time}: not a valid datetime.time object."
    #             )
    #         else:
    #             if self.logger:
    #                 self.logger.info(
    #                     f"Start time {self.start_time} validated successfully."
    #                 )
    #     else:
    #         if self.logger:
    #             self.logger.info("No start time specified.")

    # def validate_end_time(self):
    #     """
    #     Validates the `end_time` attribute of the `GLABNG` class.
    #     If `end_time` is not `None`, it checks if it is a valid `datetime.time` object.
    #     If it is not valid, it logs an error message and raises a `ValueError`.
    #     If `end_time` is valid, it logs an informational message.
    #     If `end_time` is `None`, it logs an informational message.
    #     """
    #     if self.end_time is not None:
    #         if not isinstance(self.end_time, datetime.time):
    #             if self.logger:
    #                 self.logger.error(
    #                     f"Invalid end_time {self.end_time}: not a valid datetime.time object."
    #                 )
    #             raise ValueError(
    #                 f"Invalid end_time {self.end_time}: not a valid datetime.time object."
    #             )
    #         else:
    #             if self.logger:
    #                 self.logger.info(
    #                     f"end time {self.end_time} validated successfully."
    #                 )
    #     else:
    #         if self.logger:
    #             self.logger.info("No end time specified.")

    def validate_gnss(self):
        """validates the GNSS system

        Raises:
            ValueError: when GNSS system is not in the list of GNSS systems (GREC)
        """
        # check whether the selected GNSS system is in the list of GNSS systems (GREC, or GNSS_DICT)
        if self.GNSS not in DICT_GNSS.keys():
            if self.logger:
                self.logger.error(
                    f"Invalid GNSS system {self.GNSS}: not in {''.join(DICT_GNSS.keys())}."
                )
            raise ValueError(
                f"Invalid GNSS system {self.GNSS}: not in {''.join(DICT_GNSS.keys())}."
            )
        else:
            if self.logger:
                self.logger.info(
                    f"GNSS system {DICT_GNSS[self.GNSS]} ({self.GNSS}) validated successfully."
                )

    def validate_interval(self):
        """
        Validates the `interval` attribute of the `GLABNG` class.
        If `interval` is not one of 0.1, 0.2 0.5, 1, 2, 5, 10, ...
        it logs an error message and raises a `ValueError`.
        """
        VALID_SEQUENCE = [0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 30, 60, 300]

        if not self.interval in VALID_SEQUENCE:
            if self.logger:
                self.logger.error(
                    f"Invalid interval {self.interval}: not in {VALID_SEQUENCE}."
                )
            raise ValueError(
                f"Invalid interval {self.interval}: not in {VALID_SEQUENCE}."
            )
        else:
            if self.logger:
                self.logger.info(f"Interval {self.interval} validated successfully.")

    def validate_signal_type(self):
        """
        Validates the `signal_type` attribute  against the list of valid signal types
        in DICT_SIGNAL_TYPES
        """
        # get the name of the GNSS system from DICT_GNSS
        self._gnss_name = DICT_GNSS[self.GNSS]

        # get from the DICT_SIGNAL_TYPES the list of valid signal types which
        # are in the "code" field for selected GNSS system
        valid_signal_types = [
            DICT_SIGNAL_TYPES[key]["code"]
            for key in DICT_SIGNAL_TYPES.keys()
            if not key in [23, 27] and DICT_SIGNAL_TYPES[key]["gnss"] == self._gnss_name
        ]
        print(f"valid_signal_types[{self.GNSS}]: {valid_signal_types}")

        # check whether the selected signal type is in the list of valid signal types
        if self.signal_type not in valid_signal_types:
            if self.logger:
                self.logger.error(
                    f"Invalid signal type {self.signal_type} for {self._gnss_name}: not in {valid_signal_types}."
                )
            raise ValueError(
                f"Invalid signal type {self.signal_type} for {self._gnss_name}: not in {valid_signal_types}"
                f" for {self._gnss_name}."
            )
        else:
            if self.logger:
                self.logger.info(
                    f"Signal type {self.signal_type} validated successfully."
                )

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

    def read_csv(self):
        """
        Reads the CSV file and returns a DataFrame.
        """
        if self.logger:
            self.logger.info(f"Reading CSV file {self.csv_fn}")

        df = pl.read_csv(self.csv_fn)

    def csv_gnss_sigt_df(self):
        """reads the CSV file and returns a polars DataFrame

        It uses the information for the selected GNSS, signal type and interval
        """
        if self.logger:
            self.logger.info(f"Reading CSV file {self.csv_fn}")

        # Convert interval from seconds to milliseconds
        interval_ms = self.interval * 1000
        # print(f"interval_ms: {interval_ms}")

        # Start with lazy reading
        csv_df = pl.scan_csv(self.csv_fn)

        # Chain all operations in a lazy manner
        csv_df = csv_df.filter(
            (pl.col("GNSS") == self.GNSS)
            & (pl.col("sigt") == self.signal_type)
            & (
                pl.col("TOW") % interval_ms == 0
            )  # Keep only rows that are exact multiples
        )

        return csv_df.collect()

    # def process_multiple_days(
    #     self, csv_files: list, output_file: str
    # ):
    #     # Process each file
    #     results = []
    #     for csv_file in csv_files:
    #         daily_results = analyze_cn0_values(csv_file, gnss, signal)
    #         results.append(daily_results)

    #     # Combine all results
    #     combined_df = pl.concat(results)

    #     # Sort by epoch and save to file
    #     combined_df.sort("epoch").write_csv(output_file)
