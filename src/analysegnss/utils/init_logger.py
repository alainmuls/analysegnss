# Standard library imports
import logging
from logging.handlers import TimedRotatingFileHandler
import os
from sys import stderr

# Local application imports
from analysegnss.utils.utilities import str_green


class ColorFormatter(logging.Formatter):
    # color codes
    cyan = "\x1b[36;20m"
    green = "\x1b[32;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    magenta = "\x1b[35;20m"
    # grey = "\x1b[38;20m"
    # bold_red = "\x1b[31;1m"

    COLORS = {
        logging.DEBUG: cyan,
        logging.INFO: green,
        logging.WARNING: yellow,
        logging.ERROR: red,
        logging.CRITICAL: magenta,
    }

    def format(self, record):
        reset = "\x1b[0m"
        color = self.COLORS.get(record.levelno)
        record.levelname = f"{color}{record.levelname}{reset}"
        return super().format(record)


def logger_setup(args: list, base_name: str = "logger", log_dest: str = "/tmp/logs/") -> logging.Logger:
    """creates console/time rotating file logger.
    Default logging levels are:
    - for file logging: logging.DEBUG
    - for console logging: logging.CRITICAL"""

    # create the file logger
    logger = logging.getLogger(base_name)
    logger.setLevel(logging.DEBUG)

    # always write everything to the rotating log files
    if not os.path.exists(log_dest):
        os.mkdir(log_dest)
    log_file_handler = TimedRotatingFileHandler(
        f"{log_dest}/{base_name}.log",
        when="D",
        interval=1,
        backupCount=20,
        utc=True,
        encoding="utf-8",
    )
    log_file_handler.setFormatter(
        ColorFormatter(
            "%(asctime)s [%(levelname)s](%(name)s:%(funcName)s:%(lineno)d): %(message)s"
        )
    )
    log_file_handler.setLevel(logging.DEBUG)
    logger.addHandler(log_file_handler)

    # also log to the console at a level determined by the --verbose flag
    console_handler = logging.StreamHandler(stream=stderr)  # sys.stderr
    console_handler.setLevel(
        logging.ERROR
    )  # set later by set_log_level_from_verbose() in interactive sessions
    console_handler.setFormatter(
        ColorFormatter(
            "%(asctime)s [%(levelname)s](%(name)s:%(funcName)s:%(lineno)d): %(message)s"
        )
    )
    # add the console handler to the logger
    logger.addHandler(console_handler)

    # also log to the console at a level determined by the --verbose flag
    set_log_level_from_verbose(
        logger=logger, console_handler=console_handler, args=args
    )

    print(f"{str_green(f"---------- START of {base_name} (process logged @ {log_dest}) ----------")}")
    logger.warning(f"---------- START of {base_name} (process logged @ {log_dest}) ----------")

    return logger


def set_log_level_from_verbose(
    logger: logging.Logger, console_handler: logging.StreamHandler, args: list
):
    """defines logging level for the console

    Args:
        logger (logging.Logger): logger
        console_handler (logging.StreamHandler): stream for console logging
        args (list): the verbose count defines level of logging (Not:ERROR, 1:WARNING, 2:INFO, 3:DEBUG)
    """
    # logger.info(f"args: {args}")
    if not args.verbose:
        console_handler.setLevel("ERROR")
    elif args.verbose == 1:
        console_handler.setLevel("WARNING")
    elif args.verbose == 2:
        console_handler.setLevel("INFO")
    elif args.verbose >= 3:
        console_handler.setLevel("DEBUG")
    else:
        logger.critical("UNEXPLAINED VERBOSE COUNT!")
