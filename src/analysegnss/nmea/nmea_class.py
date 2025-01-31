# Standard library imports
import argparse
from collections import defaultdict
from dataclasses import dataclass, field
import os
import logging
import sys

# Third-party imports
import polars as pl
import pynmea2
from rich.console import Console
from rich.table import Table
import utm

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
        nrfailed_parsed_lines = 0
        with open(self.nmea_ifn, "r") as file:
            for line in file:
                try:
                    msg = pynmea2.parse(line)
                    messages.append(msg)
                except pynmea2.ParseError as e:
                    if self.logger:
                        nrfailed_parsed_lines += 1
                        # self.logger.debug(f"Failed to parse line: {line.strip()} - {e}")
            self.logger.info(
                f"Successfully parsed {len(messages)} NMEA messages out of {len(messages) + nrfailed_parsed_lines} lines"
            )
        # write parsed nmea messages to file
        with open(f"{self.nmea_ifn}.nmea", "w") as file:
            for msg in messages:
                file.write(f"{msg}\n")
            self.logger.info(f"Saved parsed NMEA messages to {self.nmea_ifn}.nmea")

        return messages

    def nmea_dataframe(self, nmea_messages: list) -> pl.DataFrame:
        """
        This script collects the NMEA messages and export each field to a dataframe

        Args:
            nmea_messages (list): List of NMEA messages

        Returns:
            pl.DataFrame: DataFrame containing the collected data from the NMEA messages organized in columns
        """

        data_dict = defaultdict(
            dict
        )  # type of dict that can collect multiple fields for the same timestamp without duplicating it. (acts as a merger)
        last_timestamp = None  # most NMEA messages do not have a timestamp, so we will have to the use the last timestamp

        for msg in nmea_messages:

            # get timestamp from nmea message and update last_timstamp
            timestamp = getattr(msg, "timestamp", last_timestamp)
            if timestamp is not None:
                last_timestamp = timestamp

            # update existing list of dictionaries if timestamp already exists
            msg_entry = data_dict[timestamp]

            #TODO cast msg to correct dtype
            # Eventhough the timestamp is already saved as the key, we still store it also as a value for easier converion to dataframe
            if isinstance(msg, pynmea2.types.talker.RMC):
                msg_entry.update(
                    {
                        "datestamp": msg.datestamp,
                        "timestamp": timestamp,
                        "latitude(deg)": msg.latitude,
                        "longitude(deg)": msg.longitude,
                        "speed": msg.spd_over_grnd,
                        "track": msg.true_course,
                    }
                )
            elif isinstance(msg, pynmea2.types.talker.GGA):
                msg_entry.update(
                    {
                        "timestamp": timestamp,
                        "latitude(deg)": msg.latitude,
                        "longitude(deg)": msg.longitude,
                        "orthoH": msg.altitude,
                        "undulation": msg.geo_sep,
                        "num_sats": msg.num_sats,
                        "pvt_qual": msg.gps_qual,
                        "age(s)": msg.age_gps_data,
                    }
                )
            elif isinstance(msg, pynmea2.types.talker.GNS):
                msg_entry.update(
                    {
                        "timestamp": timestamp,
                        "latitude(deg)": msg.latitude,
                        "longitude(deg)": msg.longitude,
                        "orthoH": msg.altitude,
                        "undulation": msg.geo_sep,
                        "num_sats": msg.num_sats,
                        "age(s)": msg.age_gps_data,
                    }
                )
            elif isinstance(msg, pynmea2.types.talker.GST):
                msg_entry.update(
                    {
                        "timestamp": timestamp,
                        "rms_val": msg.rms_val,
                        "std_major(m)": msg.std_major,
                        "std_minor(m)": msg.std_minor,
                        "orientation_a(degrees_from_true_north)": msg.orient,
                        "sdlat(m)": msg.std_latitude,
                        "sdlon(m)": msg.std_longitude,
                        "sdH(m)": msg.std_dev_altitude,
                    }
                )
            elif isinstance(msg, pynmea2.types.talker.GSA):

                msg_entry.update(
                    {
                        "timestamp": timestamp,
                        "pdop": msg.pdop,
                        "hdop": msg.hdop,
                        "vdop": msg.vdop,
                    }
                )
            elif isinstance(msg, pynmea2.types.talker.GSV):
                msg_entry.update(
                    {
                        "timestamp": timestamp,
                        #'num_messages': msg.num_messages,
                        #'message_num': msg.msg_num,
                        #'nrSVs': msg.num_sv_in_view,
                    }
                )
            elif isinstance(msg, pynmea2.types.talker.VTG):
                msg_entry.update(
                    {
                        "timestamp": timestamp,
                    }
                )
            elif isinstance(msg, pynmea2.types.talker.ZDA):
                msg_entry.update(
                    {
                        "timestamp": timestamp,
                        "day": msg.day,
                        "month": msg.month,
                        "year": msg.year,
                    }
                )
            else:
                self.logger.warning(f"Unknown NMEA message type: {msg}")

        return pl.DataFrame(list(data_dict.values()))

    def add_df_column(self, nmea_df: pl.DataFrame) -> pl.DataFrame:
        """
        Check if a datetime anf UTM columns can be added to the nmea DataFrame. (note: height in NMEA messages is always orthometric (MSL))

        Args:
            nmea_df (pl.DataFrame): DataFrame containing the parsed NMEA messages

        Returns:
            pl.DataFrame: DataFrame containing the parsed NMEA messages with the added datetime UTM (easting, northing) columnsif possible
        """

        if self.logger:
            self.logger.info(
                "Trying to add datetime, UTM and orthoH columns to the NMEA parsed DataFrame"
            )

        if "datestamp" in nmea_df.columns and "timestamp" in nmea_df.columns:
            if self.logger:
                self.logger.debug(
                    "Adding datetime column to the NMEA parsed DataFrame"
                )
            nmea_df = nmea_df.with_columns(
                pl.col(
                    "datetime",
                    pl.col("datestamp").cast(pl.Date32)
                    + pl.col("timestamp").cast(pl.Time64),
                )
                .cast(pl.Datetime)
                .alias("DT")
            ).lazy()
            
        # add UTM coordinates
        if "latitude(deg)" in nmea_df.columns and "longitude(deg)" in nmea_df.columns:
            if self.logger:
                self.logger.debug(
                    "Adding UTM coordinates to the NMEA parsed DataFrame"
                )
                
            # Function to convert lat/lon in degrees to UTM
            def latlon_to_utm(lat, lon):
                easting, northing, _, _ = utm.from_latlon(lat, lon)
                return {"easting": easting, "northing": northing}

            # Apply the conversion function lazily using map_elements with specified return_dtype
            df_nmea = df_nmea.with_columns(
                pl.struct(["latitude(deg)", "longitude(deg)"])
                .apply(
                    lambda row: latlon_to_utm(
                        row["latitude(deg)"], row["longitude(deg)"]
                    ),
                    return_dtype=pl.Struct(
                        [
                            pl.Field("easting", pl.Float64),
                            pl.Field("northing", pl.Float64),
                        ]
                    ),
                )
                .alias("utm_coords")
            ).lazy()

        #TODO orthoH column is already present in the NMEA messages, however, it can't be interesting to double check if it is correct
                
        # cast nmea gnss mode/type to gnss 
        return nmea_df



    def get_dataframe(self):
        messages = self.parse_nmea_file()
        df = self.nmea_dataframe(messages)
        return df

    def rich_print_dataframe(self, df: pl.DataFrame, row_crop: int = 50):
        # Table is imported from rich.table
        table = Table(title="NMEA DataFrame (first 50 rows)")

        # Add columns
        for col in df.columns:
            table.add_column(col)

        # Add rows
        for row in df.head(row_crop).iter_rows(named=True):
            table.add_row(*[str(row[col]) for col in df.columns])

        self.rich_console.print(table)


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
        args=parsed_args, base_name=script_name, log_dest="/tmp/logs/"
    )
    nmea_parser = NMEA(nmea_ifn=parsed_args.nmea_ifn, logger=logger)
    df = nmea_parser.get_dataframe()

    # write df to csv file
    # df.write_csv(f"{parsed_args.nmea_ifn}_df.csv")

    nmea_parser.rich_print_dataframe(df)
