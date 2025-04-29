# Standard library imports
from collections import defaultdict
from collections import defaultdict
from dataclasses import dataclass, field
import datetime
import datetime
import os
import logging
import sys

# Third-party imports
import polars as pl
import pynmea2
from rich import print as rprint
from rich.console import Console
import utm

# Local application imports
from analysegnss.utils.utilities import sf64, si64
from analysegnss.gnss.standard_pnt_quality_dict import nmea_to_standard_pntqual


# TODO Only NMEA RMC contains the datestamp, so if this message is not present, the datetime can not be generated
#   This should raise an error or warning and enable the user to add the date manually
#   The NMEA ZDA message also contains the date, however day, month and year are in separate fields ...
from analysegnss.utils.utilities import sf64, si64

# TODO Only NMEA RMC contains the datestamp, so if this message is not present, the datetime can not be generated
#   This should raise an error or warning and enable the user to add the date manually
#   The NMEA ZDA message also contains the date, however day, month and year are in separate fields ...


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

            self.logger.debug(
                "Console log level set to "
                + f"{logging.getLevelName(self._console_loglevel)}"
            )

    def parse_nmea_file(self) -> list:
        """
        This script parses all the NMEA messages from a (log) file an and returns a list of NMEA messages

        args:
            nmea_ifn (str): input file name that contains NMEA messages
        returns:
            list: a list containing the parsed NMEA messages
        """
        nmea_messages = []
        nrfailed_parsed_lines = 0  # counts the non-NMEA lines
        with open(self.nmea_ifn, "r") as file:
            for line in file:
                try:
                    msg = pynmea2.parse(line)
                    nmea_messages.append(msg)
                except pynmea2.ParseError as e:
                    if self.logger:
                        nrfailed_parsed_lines += 1
                        # self.logger.debug(f"Failed to parse line: {line.strip()} - {e}")
            self.logger.info(
                f"Successfully parsed {len(nmea_messages)} NMEA messages out of {len(nmea_messages) + nrfailed_parsed_lines} lines"
            )

        # write parsed nmea messages to file
        with open(f"{self.nmea_ifn}.nmea", "w") as file:
            for msg in nmea_messages:
                file.write(f"{msg}\n")
            self.logger.info(f"Saved parsed NMEA messages to {self.nmea_ifn}.nmea")

        return nmea_messages

    def collect_nmea_values(self) -> list[dict]:
        """
        This script collects the NMEA message values and exports them to a list of dictionaries which are sorted by timestamp

        Returns:
            list: a list containing the collected data/values from the NMEA messages in dict format for each timestamp. Key of each dict is the timestamp.
                Easily Convertible to Polars DataFrame by running pl.DataFrame(list)
        """

        data_dict = defaultdict(
            dict
        )  # type of dict that can collect multiple fields for the same timestamp without duplicating it. (acts as a merger)
        last_timestamp = None  # most NMEA messages do not have a timestamp, so we will have to the use the last timestamp

        for msg in self.parse_nmea_file():

            # get timestamp from nmea message and update last_timstamp
            timestamp = getattr(msg, "timestamp", last_timestamp)
            if timestamp is not None:
                last_timestamp = timestamp

            # update existing list of dictionaries if timestamp already exists
            msg_entry = data_dict[timestamp]

            # pynmea2 doesn't always cast the values to the correct dtype,
            # so some values need to be manually casted using a safe conversion function which returns None if the cast fails without raising an error
            # we cast the values to the correct dtype now during the nmea data collection because we don't know which NMEA messages are available
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
                        "undulation": sf64(msg.geo_sep),
                        "num_sats": si64(msg.num_sats),
                        "gps_qual": si64(msg.gps_qual),
                        "age(s)": sf64(msg.age_gps_data),
                    }
                )
            elif isinstance(msg, pynmea2.types.talker.GNS):
                msg_entry.update(
                    {
                        "timestamp": timestamp,
                        "latitude(deg)": msg.latitude,
                        "longitude(deg)": msg.longitude,
                        "orthoH": msg.altitude,
                        "undulation": sf64(msg.geo_sep),
                        "num_sats": si64(msg.num_sats),
                        "age(s)": sf64(msg.age_gps_data),
                    }
                )
            elif isinstance(msg, pynmea2.types.talker.GST):
                msg_entry.update(
                    {
                        "timestamp": timestamp,
                        "rms_val": sf64(msg.rms_val),
                        "std_major(m)": sf64(msg.std_major),
                        "std_minor(m)": sf64(msg.std_minor),
                        "orientation_a(degrees_from_true_north)": sf64(msg.orient),
                        "sdlat(m)": sf64(msg.std_latitude),
                        "sdlon(m)": sf64(msg.std_longitude),
                        "sdH(m)": sf64(msg.std_dev_altitude),
                    }
                )
            elif isinstance(msg, pynmea2.types.talker.GSA):

                msg_entry.update(
                    {
                        "timestamp": timestamp,
                        "pdop": sf64(msg.pdop),
                        "hdop": sf64(msg.hdop),
                        "vdop": sf64(msg.vdop),
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
                if self.logger:
                    self.logger.warning(f"Unknown NMEA message type: {msg}")

        if self._console_loglevel <= logging.DEBUG:

            # loop through first 5 entries in data_dict
            for i, (key, value) in enumerate(data_dict.items()):
                if i < 10:
                    self.rich_console.print(
                        f"The NMEA message at timestamp {key} is: {value}"
                    )
                    self.logger.debug(
                        f"The NMEA message at timestamp {key} is: {value}"
                    )

        return list(data_dict.values())

    def get_nmea_dataframe(self) -> pl.DataFrame:
        """
        Creates a Polars DataFrame from the collected NMEA messages

        Args:
            nmea_messages (list): List of dictionaries containing the NMEA message values

        Returns:
            nmea_df( pl.DataFrame): DataFrame containing the NMEA message values organized in columns for each timestamp
        """

        # collect the NMEA values
        collected_nmea_values = self.collect_nmea_values()

        # create a DataFrame with the NMEA values per timestamp
        nmea_df = pl.DataFrame(collected_nmea_values)

        # Define dtype lookup table for each data column [ensures compatibility with the other pnt_data classes]
        dtype_lookup = {
            # Integer columns that should be uint8 (0-255)
            "num_sats": pl.UInt8,
            "gps_qual": pl.UInt8,
            "day": pl.UInt8,
            "month": pl.UInt8,
            # uint16 columns
            "year": pl.UInt16,
            # Float columns
            "latitude(deg)": pl.Float64,
            "longitude(deg)": pl.Float64,
            "orthoH": pl.Float64,
            "undulation": pl.Float64,
            "speed": pl.Float64,
            "track": pl.Float64,
            "age(s)": pl.Float64,
            "pdop": pl.Float64,
            "hdop": pl.Float64,
            "vdop": pl.Float64,
            "rms_val": pl.Float64,
            "std_major(m)": pl.Float64,
            "std_minor(m)": pl.Float64,
            "orientation_a(degrees_from_true_north)": pl.Float64,
            "sdlat(m)": pl.Float64,
            "sdlon(m)": pl.Float64,
            "sdH(m)": pl.Float64,
            # dtype Date/time columns is set in add_df_columns()
        }

        # Apply data type conversions
        for col_name, dtype in dtype_lookup.items():
            if col_name in nmea_df.columns:
                try:
                    nmea_df = nmea_df.with_columns(
                        pl.col(col_name).cast(dtype, strict=False)
                    )
                except Exception as e:
                    if self.logger:
                        self.logger.warning(
                            f"Could not cast column {col_name} to {dtype}: {e}"
                        )

        # add columns datatime and UTM coordinates if possible
        nmea_df = self.add_df_columns(nmea_df=nmea_df)

        return nmea_df

    def add_df_columns(self, nmea_df: pl.DataFrame) -> pl.DataFrame:
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

        # remove invalid PNT where GNSS quality equals 0 and add new column with general PNT quality ID from 'pnt_qual'
        if "gps_qual" in nmea_df.collect_schema().names():
            if self.logger:
                self.logger.debug("Removing invalid PNT where GNSS quality equals 0")
            nmea_df = nmea_df.filter(pl.col("gps_qual") != 0).lazy()

            # add new column with general PNT quality ID from 'pnt_qual'
            nmea_df = nmea_df.with_columns(
                pl.struct(["gps_qual"])
                .map_elements(
                    lambda x: nmea_to_standard_pntqual(x["gps_qual"]),
                    return_dtype=pl.Utf8,
                )
                .alias("pnt_qual")
            ).lazy()
            if self.logger:
                self.logger.debug(f"\tcreated new column 'pnt_qual' from 'gps_qual'")

        if (
            "datestamp" in nmea_df.collect_schema().names()
            and "timestamp" in nmea_df.collect_schema().names()
        ):

            # remove datestamp and timestamp columns with value None
            if self.logger:
                self.logger.debug(
                    "Removing datestamp and timestamp columns with value None"
                )
            nmea_df = nmea_df.filter(pl.col("datestamp").is_not_null()).lazy()
            nmea_df = nmea_df.filter(pl.col("timestamp").is_not_null()).lazy()

            if self.logger:
                self.logger.debug("Adding datetime column to the NMEA parsed DataFrame")
            nmea_df = nmea_df.with_columns(
                pl.struct(["datestamp", "timestamp"])
                .map_elements(
                    lambda row: datetime.datetime.combine(
                        row["datestamp"], row["timestamp"]
                    ),
                    return_dtype=datetime.datetime,
                )
                .alias("DT")
            ).lazy()

            # drop duplicate columns
            nmea_df = nmea_df.drop(["datestamp", "timestamp"]).lazy()

            # stage DT as first column
            first_cols = ["DT"]

        # add UTM coordinates
        if (
            "latitude(deg)" in nmea_df.collect_schema().names()
            and "longitude(deg)" in nmea_df.collect_schema().names()
        ):
            if self.logger:
                self.logger.debug("Adding UTM coordinates to the NMEA parsed DataFrame")

            # Function to convert lat/lon in degrees to UTM
            def latlon_to_utm(lat, lon):
                easting, northing, zone_number, zone_letter = utm.from_latlon(lat, lon)
                return {
                    "easting": easting,
                    "northing": northing,
                    "zone_number": zone_number,
                    "zone_letter": zone_letter,
                }

            # Apply the conversion function lazily using map_elements with specified return_dtype
            nmea_df = nmea_df.with_columns(
                pl.struct(["latitude(deg)", "longitude(deg)"])
                .map_elements(
                    lambda row: latlon_to_utm(
                        row["latitude(deg)"], row["longitude(deg)"]
                    ),
                    return_dtype=pl.Struct(
                        [
                            pl.Field("easting", pl.Float64),
                            pl.Field("northing", pl.Float64),
                            pl.Field("zone_number", pl.Int64),
                            pl.Field("zone_letter", pl.Utf8),
                        ]
                    ),
                )
                .alias("utm_coords")
            ).lazy()

            nmea_df = nmea_df.with_columns(
                [
                    pl.col("utm_coords").struct.field("easting").alias("UTM.E"),
                    pl.col("utm_coords").struct.field("northing").alias("UTM.N"),
                    pl.col("utm_coords")
                    .struct.field("zone_number")
                    .cast(pl.UInt8)
                    .alias("UTM.ZN"),
                    pl.col("utm_coords").struct.field("zone_letter").alias("UTM.ZL"),
                ]
            ).lazy()

            # drop duplicate columns
            nmea_df = nmea_df.drop(["utm_coords"]).lazy()

            # stash UTM.E and UTM.N as first columns
            first_cols.extend(["UTM.E", "UTM.N", "UTM.ZN", "UTM.ZL"])

        # add already existing columns to the first_cols list
        first_cols.extend(["latitude(deg)", "longitude(deg)", "orthoH"])

        # Get remaining columns that are not in first_cols
        remaining_cols = [
            col for col in nmea_df.collect_schema().names() if col not in first_cols
        ]

        # Reorder DataFrame
        nmea_df = nmea_df.select(first_cols + remaining_cols).lazy()

        # TODO orthoH column is already present in the NMEA messages, however, it can be interesting to double check if it is correct

        # cast nmea gnss mode/type to gnss

        if (
            getattr(nmea_df, "collect", None) is not None
        ):  # catches the error when none of the above it called for lazy operation
            with self.rich_console.status(
                "[bold green]Adding columns to the NMEA DataFrame...", spinner="dots"
            ):
                # if self.logger:
                #     self.logger.info(
                #         f"Collecting the new added columns to nmea dataframe. Be patient, this may take a while..."
                #     )

                nmea_df = nmea_df.collect()

                if self.logger:
                    self.logger.debug(nmea_df)

        return nmea_df
