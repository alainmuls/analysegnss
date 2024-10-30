import logging
import os
from dataclasses import dataclass, field


@dataclass
class RINEX:
    """class for RINEX files"""

    rnx_fn: str = field(default=None, metadata={"help": "RINEX file name"})
    logger: logging.Logger = field(default=None, metadata={"help": "logger object"})
    _console_loglevel: int = field(
        default=logging.ERROR, metadata={"help": "console log level"}
    )

    def __post_init__(self):
        self.validate_file()
        self.validate_logger_level()

    def validate_file(self):
        if not os.path.isfile(self.rnx_fn):
            if self.logger:
                self.logger.error(f"File does not exist: {self.rnx_fn}")
            raise ValueError(f"File does not exist: {self.rnx_fn}")
