import logging as logging
from logging.handlers import TimedRotatingFileHandler
import os
from utils.utilities import str_green


class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = (
        # "%(asctime)s:%(name)s:%(levelname)s:%(message)s (%(filename)s:%(lineno)d)"
        "%(asctime)s [%(levelname)s](%(name)s:%(filename)s%(funcName)s:%(lineno)d): %(message)s"
    )

    # TODO: test the color output for logger
    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def logger_setup(args: list, base_name: str = "logger", log_dir: str = "logs") -> logging.Logger:
    """creates console/time rotating file logger.
    Default logging levels are:
    - for file logging: logging.DEBUG
    - for console logging: logging.CRITICAL"""

    # create the file logger
    logger = logging.getLogger(base_name)
    logger.setLevel(logging.DEBUG)

    # always write everything to the rotating log files
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    log_file_handler = TimedRotatingFileHandler(
        f"{log_dir}/{base_name}.log",
        when="D",
        interval=1,
        backupCount=20,
        utc=True,
        encoding="utf-8",
    )
    log_file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s](%(name)s:%(funcName)s:%(lineno)d): %(message)s"
        )
    )
    log_file_handler.setLevel(logging.DEBUG)
    logger.addHandler(log_file_handler)

    # also log to the console at a level determined by the --verbose flag
    console_handler = logging.StreamHandler()  # sys.stderr
    # console_handler.setLevel(
    #     logging.CRITICAL
    # )  # set later by set_log_level_from_verbose() in interactive sessions
    console_handler.setFormatter(
        # logging.Formatter("[%(levelname)s](%(funcName)s:%(lineno)d): %(message)s")
        CustomFormatter()
    )
    logger.addHandler(console_handler)

    # also log to the console at a level determined by the --verbose flag
    set_log_level_from_verbose(
        logger=logger, console_handler=console_handler, args=args
    )

    logger.info(f"---------- {str_green('start')} {str_green(base_name)} -------------")

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
