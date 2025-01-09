import datetime
import logging
import os
import sys
from dataclasses import dataclass, field

from analysegnss.config import GNSS_DICT, console
from analysegnss.utils.utilities import locate, str_red


@dataclass
class RINEX:
    """general class for RINEX files"""

    gnss: str = field(default=None, metadata={"help": "select multiple from GREC"})

    start_time: datetime.time = field(default=None, metadata={"help": "start time"})
    end_time: datetime.time = field(default=None, metadata={"help": "end time"})

    logger: logging.Logger = field(default=None, metadata={"help": "logger object"})
    _console_loglevel: int = field(
        default=logging.ERROR, metadata={"help": "console log level"}
    )
    console: Console = field(default=None, metadata={"help": "console object"})

    def __post_init__(self):
        # Add this at the start of post_init
        if self.console is None:
            self.console = console

        self.validate_gnss()
        self.validate_start_time()
        self.validate_end_time()
        self.validate_logger_level()
        self.validate_permissions()

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

    def validate_permissions(self):
        # Locate and validate gfzrnx executable
        self.gfzrnx_exe = locate("gfzrnx")
        if not os.access(self.gfzrnx_exe, os.X_OK):
            if self.logger:
                self.logger.error(
                    f"No execute permission for gfzrnx at: {self.gfzrnx_exe}"
                )
            raise PermissionError(
                f"No execute permission for gfzrnx at: {self.gfzrnx_exe}"
            )
