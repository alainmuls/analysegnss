import datetime
import logging
import os
import sys
from dataclasses import dataclass, field

from analysegnss.config import ERROR_CODES
from analysegnss.utils.utilities import str_red, str_yellow


@dataclass
class GLABNG:
    glab_fn: str = field(default=None)
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
        """Validate existence and readability of gLAB file

        Raises:
            ValueError: when file doesn't exist or isn't readable
        """
        # Check if file exists and is readable
        if not os.path.isfile(self.glab_fn) or not os.access(self.glab_fn, os.R_OK):
            if self.logger:
                self.logger.error(
                    f"File does not exist or is not readable: {str_red(self.glab_fn)}"
                )
            raise ValueError(
                f"File does not exist or is not readable: {str_red(self.glab_fn)}"
            )

        # Check for OUTPUT lines
        has_output_lines = False
        with open(self.glab_fn, "r") as f:
            for line in f:
                if line.startswith("OUTPUT"):
                    has_output_lines = True
                    break

        if not has_output_lines:
            if self.logger:
                self.logger.error(
                    f"File contains no OUTPUT lines: {str_red(self.glab_fn)}"
                )
            raise ValueError(f"File contains no OUTPUT lines: {str_red(self.glab_fn)}")

    def validate_start_time(self):
        """
        Validates the `start_time` attribute of the `GLABNG` class.
        If `start_time` is not `None`, it checks if it is a valid `datetime.time` object.
        If it is not valid, it logs an error message and raises a `ValueError`.
        If `start_time` is valid, it logs an informational message.
        If `start_time` is `None`, it logs an informational message.
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
        Validates the `end_time` attribute of the `GLABNG` class.
        If `end_time` is not `None`, it checks if it is a valid `datetime.time` object.
        If it is not valid, it logs an error message and raises a `ValueError`.
        If `end_time` is valid, it logs an informational message.
        If `end_time` is `None`, it logs an informational message.
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

    def glab_dataframe(self, lst_sections: list[str] = ["OUTPUT"]) -> dict:
        """parses specified sections from gLAB file and returns a dictionary of dataframes
        where the section name is the key and the dataframe is the value

        Args:
            lst_sections (list[str], optional): list of sections to parse. Defaults to ["OUTPUT"].

        Returns:
            dict: key is section name and value is dataframe
        """
        if not lst_sections:
            lst_sections = ["OUTPUT"]  # Set default if empty list provided

        # Check which sections exist in file
        valid_sections = []
        with open(self.glab_fn, "r") as f:
            content = f.read()
            for section in lst_sections:
                if section in content:
                    valid_sections.append(section)
                else:
                    if self.logger:
                        self.logger.warning(
                            f"Section '{str_red(section)}' not found in {str_yellow(self.glab_fn)}, skipping"
                        )

        for glab_section in valid_sections:
            # read the glab_fn file and just use the lines that start with glab_section
            section_data = []
            with open(self.glab_fn, "r") as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith(glab_section):
                        section_data.append(line)
