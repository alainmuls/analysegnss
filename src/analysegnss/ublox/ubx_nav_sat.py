import csv
import logging
from pyubx2.ubxmessage import UBXMessage  # For type hinting

# Assuming str_yellow is available in your project utils
from analysegnss.utils.utilities import str_yellow


class UBX_NAV_SAT:
    """
    Manages the decoding of uBlox UBX-NAV-SAT messages (0x01 0x35)
    and writing of the data to a CSV file.
    Each row in the CSV corresponds to one satellite observation from a NAV-SAT message.
    """

    def __init__(self, fn_nav_sat: str = "/tmp/ubx_nav_sat.csv") -> None:
        """
        Initializes an instance of UBX_NAV_SAT.

        Args:
            fn_nav_sat (str): The path to the CSV file where NAV-SAT data will be stored.
        """
        self.logger = logging.getLogger("ubx_parser")

        # Message-level fields that are common to all satellites in a single message
        self.message_level_fields = ["iTOW", "version"]

        # Per-satellite fields. pyubx2 will provide these with a suffix like _01, _02, ...
        # These are the base names.
        self.satellite_level_fields = [
            "gnssId",  # GNSS identifier (e.g., 0=GPS, 2=Galileo, 3=BeiDou, 6=GLONASS)
            "svId",  # Satellite identifier
            "cno",  # Carrier to noise ratio (signal strength) (dBHz)
            "elev",  # Elevation (deg)
            "azim",  # Azimuth (deg)
            "prRes",  # Pseudorange residual (cm) - will be converted to meters
            "flags",  # Raw flags bitmask
            # Fields below are typically parsed by pyubx2 from the 'flags' bitmask
            "qualityInd",  # Signal quality indicator (0-7)
            "svUsed",  # Satellite is used for navigation (1=yes, 0=no)
            "health",  # Satellite health status (e.g., 0=unknown, 1=healthy, 2=unhealthy)
            "doppAvail",  # Doppler is available for this SV (1=yes)
            "prAvail",  # Pseudorange is available for this SV (1=yes)
            "crAvail",  # Carrier range is available for this SV (1=yes)
            "drAvail",  # Delta range is available for this SV (1=yes)
            "anoAvail",  # Autonomous navigation data is available (e.g., ephemeris)
        ]

        # The full list of fields for the CSV header
        self.csv_header_fields = self.message_level_fields + self.satellite_level_fields

        self.fn_nav_sat = fn_nav_sat
        try:
            # Use newline='' to prevent blank rows in CSV on Windows
            self.fd_nav_sat = open(self.fn_nav_sat, "w", newline="")
            self.writer = csv.writer(self.fd_nav_sat, delimiter=",")
            self.init_csv_header()
            self.logger.info(
                f"{str_yellow('UBX_NAV_SAT')} initialized, writing to {self.fn_nav_sat}"
            )
        except IOError as e:
            self.logger.error(
                f"Failed to open file {self.fn_nav_sat} for UBX_NAV_SAT: {e}"
            )
            self.writer = None  # type: ignore
            self.fd_nav_sat = None  # type: ignore
            raise  # Re-raise the exception

    def init_csv_header(self) -> None:
        """Initializes the CSV header for NAV-SAT data."""
        if self.writer and self.fd_nav_sat:
            self.writer.writerow(self.csv_header_fields)
            self.fd_nav_sat.flush()

    def decode_sat(self, sat_msg: UBXMessage) -> None:
        """
        Decodes a UBX-NAV-SAT message and writes its satellite data to the CSV file.
        One row is written per satellite.

        Args:
            sat_msg (UBXMessage): A parsed UBX-NAV-SAT message object.
        """
        if not self.writer:
            self.logger.error(
                "CSV writer not initialized for NAV-SAT. Cannot write data."
            )
            return

        if sat_msg.identity != "NAV-SAT":
            self.logger.warning(
                f"Attempted to decode a non NAV-SAT message ({sat_msg.identity}) with decode_sat."
            )
            return

        itow = getattr(sat_msg, "iTOW", None)
        version = getattr(sat_msg, "version", None)
        num_svs = getattr(sat_msg, "numSvs", 0)

        for i in range(num_svs):
            # pyubx2 uses 1-based indexing for satellite blocks, e.g., gnssId_01, svId_01
            sv_idx_str = f"_{i+1:02d}"  # Formats to _01, _02, ..., _10, etc.

            # Start with common message-level data for this satellite's row
            current_row_data = [itow, version]

            for base_field_name in self.satellite_level_fields:
                actual_field_name = base_field_name + sv_idx_str
                value = getattr(sat_msg, actual_field_name, None)

                if base_field_name == "prRes" and value is not None:
                    try:
                        current_row_data.append(value / 100.0)  # Convert cm to meters
                    except TypeError:
                        self.logger.warning(
                            f"NAV-SAT: Could not convert prRes for SV {sv_idx_str}, value: {value}"
                        )
                        current_row_data.append(
                            value
                        )  # Append original problematic value
                else:
                    current_row_data.append(value)

            self.writer.writerow(current_row_data)

        if self.fd_nav_sat and num_svs > 0:  # Flush if data was potentially written
            self.fd_nav_sat.flush()

    def close(self) -> None:
        """Closes the CSV file."""
        if self.fd_nav_sat and not self.fd_nav_sat.closed:
            self.fd_nav_sat.close()
            self.logger.info(f"UBX_NAV_SAT CSV file '{self.fn_nav_sat}' closed.")

    def __del__(self) -> None:
        """Ensures the file is closed when the object is garbage collected."""
        try:
            if (
                hasattr(self, "fd_nav_sat")
                and self.fd_nav_sat
                and not self.fd_nav_sat.closed
            ):
                self.fd_nav_sat.close()
        except Exception:
            # Suppress exceptions in __del__
            pass
