import datetime
import logging
import os
import re
import sys
from dataclasses import dataclass, field

import polars as pl
import utm

from analysegnss.config import GEOID_PATH
from analysegnss.glabng.glab_msg_headers import GLAB_OUTPUTS
from analysegnss.gnss import geoid
from analysegnss.utils.utilities import str_red, str_yellow


@dataclass
class GLABNG:
    glab_ifn: str = field(default=None)
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
        if not os.path.isfile(self.glab_ifn) or not os.access(self.glab_ifn, os.R_OK):
            if self.logger:
                self.logger.error(
                    f"File does not exist or is not readable: {str_red(self.glab_ifn)}"
                )
            raise ValueError(
                f"File does not exist or is not readable: {str_red(self.glab_ifn)}"
            )

        # Check for OUTPUT lines
        has_output_lines = False
        with open(self.glab_ifn, "r") as f:
            for line in f:
                if line.startswith("OUTPUT"):
                    has_output_lines = True
                    break

        if not has_output_lines:
            if self.logger:
                self.logger.error(
                    f"File contains no OUTPUT lines: {str_red(self.glab_ifn)}"
                )
            raise ValueError(f"File contains no OUTPUT lines: {str_red(self.glab_ifn)}")

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
        with open(self.glab_ifn, "r") as f:
            lines = f.readlines()
            for section in lst_sections:
                if any(line.startswith(section) for line in lines):
                    valid_sections.append(section)
                else:
                    if self.logger:
                        self.logger.warning(
                            f"Section '{str_red(section)}' not found in {str_yellow(self.glab_ifn)}, skipping"
                        )

        section_dfs = {}  # dict with glabng section name and dataframe"
        for glab_section in valid_sections:
            # read the glab_ifn file and just use the lines that start with glab_section
            section_data = []
            with open(self.glab_ifn, "r") as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith(glab_section):
                        # Match quoted strings and split rest on spaces
                        parts = []
                        quote_match = re.search(r'"([^"]*)"', line)
                        if quote_match:
                            # Split everything before the quote
                            pre_quote = line[: quote_match.start()].split()
                            parts.extend(pre_quote)
                            # Add the quoted part as a single field
                            parts.append(quote_match.group(1))
                        else:
                            # If no quotes, just split normally
                            parts = line.split()
                        section_data.append(parts)

            # print the section_data
            # print(section_data[:3])

            df = self.load_section_data(section=glab_section, section_data=section_data)
            section_dfs[glab_section] = df

        return section_dfs

    def load_section_data(self, section: str, section_data: list[str]) -> pl.DataFrame:
        """loads a specific section of a gLAB file into a polars dataframe

        Args:
            section (str): identifier of the section to load
            section_data (list[str]): data for this specific section

        Returns:
            pl.DataFrame: dataframe with the data from the section
        """

        def latlon_to_utm(lat: float, lon: float) -> dict:
            """converts latitude and longitude to UTM coordinates

            Args:
                lat (float): latitude in degrees
                lon (float): longitude in degrees

            Returns:
                dict: containing UTM coordinates
            """
            easting, northing, _, _ = utm.from_latlon(lat, lon)
            return {"easting": easting, "northing": northing}

        # Create schema dictionary
        schema = {}
        for k, v in GLAB_OUTPUTS[section].items():
            schema[k] = v["dtype"]

        # Load data into polars DataFrame
        df_section = pl.DataFrame(section_data, schema=schema).lazy()

        # Filter columns based on 'keep' field
        columns_to_keep = [
            col for col, props in GLAB_OUTPUTS[section].items() if props["keep"]
        ]
        df_section = df_section.select(columns_to_keep)

        # Convert YEAR, DOY and SOD to datetime if present

        df_section = df_section.with_columns(
            pl.struct(["Year", "DOY", "SOD"])
            .apply(
                lambda x: datetime.datetime(year=int(x["Year"]), month=1, day=1)
                + datetime.timedelta(days=int(x["DOY"]) - 1, seconds=float(x["SOD"])),
                return_dtype=pl.Datetime,
            )
            .alias("DT")
        ).lazy()

        # Add UTM coordinates and orthometric height if section is OUTPUT
        if section == "OUTPUT":
            if self.logger:
                self.logger.info("\tadding UTM coordinates to the dataframe")
                self.logger.info(
                    "\tadding geoid undulation & orthometric height to the dataframe"
                )

            # Initialize geoid model
            gh_model = geoid.GeoidHeight(GEOID_PATH)

            # Add UTM coordinates
            df_section = df_section.with_columns(
                pl.struct(["lat", "lon"])
                .apply(
                    lambda row: latlon_to_utm(row["lat"], row["lon"]),
                    return_dtype=pl.Struct(
                        [
                            pl.Field("easting", pl.Float64),
                            pl.Field("northing", pl.Float64),
                        ]
                    ),
                )
                .alias("utm_coords")
            ).lazy()

            # Extract UTM coordinates
            df_section = df_section.with_columns(
                [
                    pl.col("utm_coords").struct.field("easting").alias("UTM.E"),
                    pl.col("utm_coords").struct.field("northing").alias("UTM.N"),
                ]
            ).lazy()

            # Add geoid undulation
            df_section = df_section.with_columns(
                pl.struct(["lat", "lon"])
                .apply(
                    lambda x: gh_model.get(x["lat"], x["lon"], gh_model),
                    return_dtype=pl.Float64,
                )
                .alias("undulation")
            ).lazy()

            # Calculate orthometric height
            df_section = df_section.with_columns(
                pl.struct(["ellH", "undulation"])
                .apply(lambda x: x["ellH"] - x["undulation"], return_dtype=pl.Float64)
                .alias("orthoH")
            ).lazy()

            # Clean up intermediate columns
            df_section = df_section.drop(["Year", "DOY", "SOD", "utm_coords"]).lazy()

        return df_section.collect()
