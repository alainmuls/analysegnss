# Standard library imports
import datetime
import logging
import os
import sys
from dataclasses import dataclass, field

# Local imports
from analysegnss.utils.utilities import str_red


@dataclass
class UBX:
    ubx_fn: str = field(default=None)
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
        if not self.ubx_fn:
            if self.logger:
                self.logger.error("UBX filename (ubx_fn) cannot be None.")
            raise ValueError("UBX filename (ubx_fn) cannot be None.")

        if not os.path.isfile(self.ubx_fn):
            if self.logger:
                self.logger.error(f"File does not exist: {self.ubx_fn}")
            raise ValueError(f"File does not exist: {self.ubx_fn}")

        found_preamble = False
        preamble_position = -1
        preamble = b"\xb5\x62"
        preamble_len = len(preamble)

        try:
            with open(self.ubx_fn, "rb") as f:
                chunk_size = 4096  # Read 4KB at a time
                overlap = b""
                current_file_pos = 0  # Tracks the start position of the new data read in each iteration

                while True:
                    data_read = f.read(chunk_size)
                    # If no new data read and no overlap left, we're done
                    if not data_read and not overlap:
                        break

                    current_chunk = overlap + data_read

                    # This case should ideally not be hit if the loop condition above is correct
                    if not current_chunk:
                        break

                    idx = current_chunk.find(preamble)

                    if idx != -1:
                        found_preamble = True
                        # Calculate absolute position of preamble in the file
                        preamble_position = (current_file_pos - len(overlap)) + idx
                        break  # Found the first occurrence

                    # If EOF reached and preamble not found in the last processed chunk
                    if not data_read:
                        break

                    # Prepare overlap for the next iteration:
                    # These are the last (preamble_len - 1) bytes of the current_chunk
                    if (
                        len(current_chunk) >= preamble_len
                    ):  # Ensure current_chunk is long enough
                        overlap = current_chunk[-(preamble_len - 1) :]
                    else:  # current_chunk is shorter than preamble_len -1, so keep all of it
                        overlap = current_chunk

                    current_file_pos += len(data_read)
        except IOError as e:
            if self.logger:
                self.logger.error(f"Error opening or reading file {self.ubx_fn}: {e}")
            raise ValueError(f"Could not read file {self.ubx_fn}: {e}")

        if found_preamble:
            if self.logger:
                if preamble_position == 0:
                    self.logger.debug(
                        f"UBX preamble {preamble!r} found at the beginning of {self.ubx_fn}."
                    )
                else:
                    self.logger.info(
                        f"UBX preamble {preamble!r} found at offset {preamble_position} in {self.ubx_fn}. Data before this offset might be non-UBX."
                    )
                self.logger.debug(
                    f"File validation: UBX preamble presence confirmed in {self.ubx_fn}."
                )
        else:
            if self.logger:
                self.logger.warning(
                    f"UBX preamble {preamble!r} not found in {self.ubx_fn}. The file may not be a valid UBX stream or is corrupted."
                )
            # Depending on strictness, you might want to raise ValueError here.
            # Sticking to a warning if not found.

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
                        f"End time {self.end_time} validated successfully."
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
                    self._console_loglevel = handler.level
                    break  # Found one, no need to check others

            self.logger.debug(
                "Console log level set to "
                + f"{str_red(logging.getLevelName(self._console_loglevel))}"
            )
