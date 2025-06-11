import csv
import logging

from pyubx2.ubxmessage import UBXMessage  # Import UBXMessage for type hinting

from analysegnss.utils.utilities import str_yellow, str_red
from analysegnss.ublox.ubx_definitions import (
    convert_ublox_gnss_identifier,
    get_ublox_signal_details,
)


class UBX_NAV_POSLLH:
    """
    Class to handle the uBlox NAV-POSLLH message (0xB5 0x62 0x01 0x02)
    and writing of the data to a CSV file.
    """

    def __init__(self, fn_posllh: str = "/tmp/ubx_nav_posllh.csv") -> None:
        """
        Initialize the UBX_NAV_POSLLH class.

        Args:
            fn_posllh (str): Path to the CSV file where NAV-POSLLH data will be written.
        """
        self.logger = logging.getLogger("ubx_parser")

        # Define the fields for NAV-POSLLH message
        self.posllh_fields = [
            "iTOW",
            "lon",
            "lat",
            "height",
            "hMSL",
            "hAcc",
            "vAcc",
        ]

        # Fields that need to be converted from mm to m
        self.fields_to_convert = {
            "height",
            "hMSL",
            "hAcc",
            "vAcc",
        }

        self.fn_posllh = fn_posllh
        # Write the header line to the NAV-POSLLH csv file
        self.fd_posllh = open(fn_posllh, "w", newline="")
        self.writer = csv.writer(self.fd_posllh, delimiter=",")
        self.init_csv_header()

    def init_csv_header(self):
        """Initializes the csv header for NAV-POSLLH."""
        self.writer.writerow(self.posllh_fields)
        self.fd_posllh.flush()

    def decode_posllh(self, nav_posllh: UBXMessage) -> None:
        """Decodes the NAV-POSLLH message and writes the data to the csv file.

        Args:
            nav_posllh (UBXMessage): NAV-POSLLH parsed UBXMessage object
        """
        # Check if all essential attributes are present
        if not all(hasattr(nav_posllh, attr) for attr in self.posllh_fields):
            missing_attrs = [
                attr for attr in self.posllh_fields if not hasattr(nav_posllh, attr)
            ]
            self.logger.error(
                f"Missing essential attributes in NAV-POSLLH message: {', '.join(missing_attrs)}"
            )
            return

        # # Extract values using the defined fields and write to CSV
        row_data = []
        for field in self.posllh_fields:
            value = getattr(nav_posllh, field, None)
            if field in self.fields_to_convert and value is not None:
                try:
                    row_data.append(value / 1000)
                except TypeError:
                    # Handle cases where value might not be numeric, though unlikely for these fields
                    self.logger.warning(
                        f"Could not divide value for field {field} as it's not numeric: {value}"
                    )
                    row_data.append(
                        value
                    )  # Append original value or None/specific placeholder
            else:
                row_data.append(value)

        self.writer.writerow(row_data)
        self.fd_posllh.flush()

    def close(self) -> None:
        """Closes the CSV file."""
        if self.fd_posllh and not self.fd_posllh.closed:
            self.fd_posllh.close()
            if self.logger:
                self.logger.info(f"UBX_NAV_DOP CSV file for DOP data closed.")

    def __del__(self) -> None:
        """Ensures the file is closed when the object is garbage collected."""
        try:
            if hasattr(self, "df_dop") and self.fd_posllh and not self.fd_posllh.closed:
                self.fd_posllh.close()
        except Exception:
            # It's generally good practice to suppress exceptions in __del__
            # as the logger might not be available during interpreter shutdown.
            pass
