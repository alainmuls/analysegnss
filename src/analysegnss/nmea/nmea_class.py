# Standard library imports
import argparse
from dataclasses import dataclass, field
import os
import logging
import sys

# Third-party imports
import polars as pl
import pynmea2
from rich.console import Console

# Local application imports
from analysegnss.utils import argument_parser, init_logger

@dataclass
class NMEA:
    nmea_ifn: str = field(default=None)
    logger: logging.Logger = field(default=None)
    _console_loglevel: int = field(default=logging.ERROR)
    rich_console: Console = field(default=Console())

    def __post_init__(self):
        self.validate_file()

    def validate_file(self):
        if not os.path.isfile(self.nmea_ifn):
            if self.logger:
                self.logger.error(f"File does not exist: {self.nmea_ifn}")
            raise ValueError(f"File does not exist: {self.nmea_ifn}")

    def parse_nmea_file(self):
        messages = []
        with open(self.nmea_ifn, 'r') as file:
            for line in file:
                try:
                    msg = pynmea2.parse(line)
                    messages.append(msg)
                except pynmea2.ParseError as e:
                    if self.logger:
                        self.logger.warning(f"Failed to parse line: {line.strip()} - {e}")
            self.logger.info(f"Successfully parsed {len(messages)} NMEA messages") 
        # write parsed nmea messages to file
        with open(f'{self.nmea_ifn}.nmea', 'w') as file:
            for msg in messages:
                file.write(f"{msg}\n")
            self.logger.info(f"Saved parsed NMEA messages to {self.nmea_ifn}.nmea")
        
        return messages

    def nmea_dataframe(self, nmea_messages: list):
        data = []
        for msg in nmea_messages:
            if isinstance(msg, pynmea2.types.talker.GGA):
                data.append({
                    'timestamp': msg.timestamp,
                    'latitude': msg.latitude,
                    'longitude': msg.longitude,
                    'altitude': msg.altitude,
                    'num_sats': msg.num_sats,
                    'gps_qual': msg.gps_qual,
                })
        return pl.DataFrame(data)

    def get_dataframe(self):
        messages = self.parse_nmea_file()
        df = self.nmea_dataframe(messages)
        return df



def argument_parser_nmea_class(args: list, script_name: str) -> argparse.Namespace:
    """
    Parses the arguments and creates console/file logger for nmea_class.py
    """

    baseName = script_name

    help_text = (
        baseName
        + """
        Parses NMEA strings from a file and saves the output to a
        The output contains:
            - the NMEA strings
            - the NMEA strings split into their individual components
    """
    )

    parser = argparse.ArgumentParser(description=help_text)
    parser.add_argument("-V", "--version", action="version", version="%(prog)s v0.2")
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=None,
        help="verbose level... repeat up to three times.",
        required=False,
    )
    parser.add_argument(
        "--log_dest",
        help="Specify log destination directory (full path). (Default is /tmp/logs/)",
        type=str,
        required=False,
        default="/tmp/logs/",
    )
    ############################################
    parser.add_argument(
        "-ifn",
        "--nmea_ifn",
        help="Input file name that contain NMEA messages.",
        type=str,
        required=True,
    )

    args = parser.parse_args(args)

    return args



# Example usage
if __name__ == "__main__":
    # get name of script
    script_name = os.path.basename(__file__).split(".")[0]
    
    # parse arguments
    parsed_args = argument_parser_nmea_class(args=sys.argv[1:], script_name=script_name)
    
    logger = init_logger.logger_setup(
        args=parsed_args, base_name=script_name, log_dest='/tmp/logs/'
    )
    nmea_parser = NMEA(nmea_ifn=parsed_args.nmea_ifn, logger=logger)
    df = nmea_parser.get_dataframe()
    print(df)