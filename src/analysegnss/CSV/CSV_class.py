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
from rich import print
from rich.console import Console

from analysegnss.config import ERROR_CODES, GNSS_DICT
from analysegnss.gnss.gnss_dt import gpsms2dt
from analysegnss.sbf import sbf_constants as sbfc
from analysegnss.utils.utilities import locate, str_red, str_yellow


@dataclass
class GNSS_CSV:
    csv_fn: str = field(default=None)
    # start_time: datetime.time = field(default=None)
    # end_time: datetime.time = field(default=None)
    GNSS: str = field(default="G")
    interval: float = field(default=10.0)

    logger: logging.Logger = field(default=None)
    _console_loglevel: int = field(default=logging.ERROR)
    rich_console: Console = field(default=Console())

    def __post_init__(self):
        self.validate_file()
        # self.validate_start_time()
        # self.validate_end_time()
        self.validate_gnss()
        self.validate_interval()
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
        if self.GNSS not in GNSS_DICT.keys():
            if self.logger:
                self.logger.error(
                    f"Invalid GNSS system {self.GNSS}: not in {GNSS_DICT.keys()}."
                )
            raise ValueError(
                f"Invalid GNSS system {self.GNSS}: not in {GNSS_DICT.keys()}."
            )
        else:
            if self.logger:
                self.logger.info(
                    f"GNSS system {GNSS_DICT[self.GNSS]} ({self.GNSS}) validated successfully."
                )

    def validate_interval(self):
        """
        Validates the `interval` attribute of the `GLABNG` class.
        If `interval` is not one of 0.1, 0.2 0.5, 1, 2, 5, 10, ...
        it logs an error message and raises a `ValueError`.
        """
        VALID_SEQUENCE = [0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 300]

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
