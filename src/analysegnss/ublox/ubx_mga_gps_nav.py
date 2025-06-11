import csv
import logging
import math  # Added for math.pi

from pyubx2.ubxmessage import UBXMessage  # Import UBXMessage for type hinting

from analysegnss.utils.utilities import str_yellow, str_red
from analysegnss.ublox.ubx_definitions import (
    convert_ublox_gnss_identifier,
    get_ublox_signal_details,
)


class UBX_MGA_GPS_EPH:
    """
    Class to handle the uBlox MGA-GPS-EPH message (0xB5 0x62 0x13 0x00)
    and writing of the data to a CSV file.
    """

    def __init__(self, fn_eph: str = "/tmp/ubx_mga_gps_eph.csv") -> None:
        """
        Initialize the UBX_MGA_GPS_EPH class.

        Args:
            fn_eph (str): Path to the CSV file where MGA-GPS-EPH data will be written.
        """
        self.logger = logging.getLogger("ubx_parser")

        self.fn_eph = fn_eph
        try:
            # Use newline='' to prevent blank rows in CSV on Windows
            self.fd_eph = open(self.fn_eph, "w", newline="")
            self.writer = csv.writer(self.fd_eph, delimiter=",")
            # self.init_csv_header() # Called later after dict_gps_nav is defined
        except IOError as e:
            self.logger.error(
                f"Failed to open file {self.fn_eph} for UBX_MGA_GPS_EPH: {e}"
            )
            # To prevent further errors, ensure writer is not used if file opening failed
            self.writer = None  # type: ignore
            self.fd_eph = None  # type: ignore
            raise  # Re-raise the exception so the caller is aware

        # List defining the ordered fields for the CSV header for GPS ephemeris data.
        # pyubx2 attribute names might differ slightly from these CSV headers (e.g. eccen -> ecc).
        self.gps_eph_fields = [
            "GNSS",
            "PRN",
            "TOW",  # Note: MGA-GPS-EPH messages (type 0) don't contain iTOW.
            "WNa",
            "URA",
            "SVHealth",
            "tgd",
            "IODC",
            "toc",
            "af0",
            "af1",
            "af2",
            "Crs",
            "DeltaN",
            "M0",
            "Cuc",
            "Cus",
            "eccen",
            "sqrtA",
            "Toe",
            "Cic",
            "Omega0",
            "Cis",
            "Crc",
            "i0",
            "omega",
            "OmegaDot",
            "IDOT",
        ]

        # Fields that are in radians (or rad/s) and need to be converted to degrees (or deg/s)
        self.fields_to_convert = {
            "DeltaN",
            "M0",
            "Omega0",
            "i0",
            "omega",
            "OmegaDot",
            "IDOT",
        }

        if self.writer:  # Ensure writer was initialized
            self.init_csv_header()
            self.logger.info(
                f"{str_yellow('UBX_MGA_GPS_EPH')} initialized, writing to {self.fn_eph}"
            )

    def init_csv_header(self):
        """initializes the csv header for UBX message MGA_GPS_EPH"""
        if self.writer and self.fd_eph:
            self.writer.writerow(self.gps_eph_fields)
            self.fd_eph.flush()

    def decode_eph(self, mga_gps_eph_msg: UBXMessage) -> None:
        """
        Decodes a UBX-MGA-GPS ephemeris message and writes its data to the CSV file.

        Args:
            mga_gps_eph_msg (UBXMessage): A parsed UBX-MGA-GPS message object
            (specifically type 0 for ephemeris).
        """
        if not self.writer:
            self.logger.error(
                "CSV writer not initialized for MGA-GPS-EPH. Cannot write data."
            )
            return

        # MGA-GPS messages have a 'type' field. Type 0 is for GPS Ephemeris.
        # pyubx2 identity for 0x13 0x00 is 'MGA-GPS'.
        if (
            mga_gps_eph_msg.identity != "MGA-GPS"
            or getattr(mga_gps_eph_msg, "type", -1) != 0
        ):
            self.logger.warning(
                f"Attempted to decode a non MGA-GPS-Ephemeris message "
                f"({mga_gps_eph_msg.identity}, type {getattr(mga_gps_eph_msg, 'type', 'N/A')}) "
                f"with decode_eph."
            )
            return

        row_data = []
        # Map CSV headers to pyubx2 attribute names where they differ
        # and handle special cases like 'GNSS' and 'TOW'.
        # Standard GPS ephemeris parameters are typically direct attributes.
        attribute_map = {
            "PRN": "svId",
            "WNa": "wn",
            "URA": "ura",
            "SVHealth": "health",  # u-blox 'health' field for SV health
            "DeltaN": "deltan",
            "eccen": "ecc",
            "sqrtA": "sqrta",
            "Omega0": "omega0",
            "OmegaDot": "omegadot",
            # Other keys in dict_gps_nav are assumed to match attribute names
        }

        for header in self.gps_eph_fields:
            if header == "GNSS":
                row_data.append("G")  # GPS
            elif header == "TOW":
                # MGA-GPS ephemeris messages (type 0) do not contain iTOW.
                # Log as None or a placeholder if required by CSV structure.
                row_data.append(getattr(mga_gps_eph_msg, "iTOW", None))
            else:
                attr_name = attribute_map.get(
                    header, header.lower()
                )  # Default to lowercased header
                value = getattr(mga_gps_eph_msg, attr_name, None)

                if header in self.fields_to_convert and value is not None:
                    try:
                        # Convert radians (or rad/s) to degrees (or deg/s)
                        converted_value = value * (180.0 / math.pi)
                        row_data.append(converted_value)
                    except TypeError:
                        if self.logger:  # Check if logger exists
                            self.logger.warning(
                                f"MGA-GPS-EPH: Could not convert field '{header}' to degrees "
                                f"as value is not numeric: {value}. Appending original."
                            )
                        row_data.append(
                            value
                        )  # Append original value if conversion fails
                else:
                    row_data.append(value)

        self.writer.writerow(row_data)
        if self.fd_eph:
            self.fd_eph.flush()

    def close(self) -> None:
        """Closes the CSV file."""
        if self.fd_eph and not self.fd_eph.closed:
            self.fd_eph.close()
            if (
                self.logger
            ):  # Check if logger exists, as it might be None during __del__
                self.logger.info(f"UBX_MGA_GPS_EPH CSV file '{self.fn_eph}' closed.")

    def __del__(self) -> None:
        """Ensures the file is closed when the object is garbage collected."""
        try:
            # Check if fd_eph was initialized and is still open
            if hasattr(self, "fd_eph") and self.fd_eph and not self.fd_eph.closed:
                self.fd_eph.close()
        except Exception:
            # Suppress exceptions in __del__ as the logging state can be unpredictable
            # during interpreter shutdown, and file handles might already be invalid.
            pass
