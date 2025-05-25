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

        # Write the header line to the NAV-POSLLH csv file
        self.fd_posllh = open(fn_posllh, "w")
        self.writer = csv.writer(self.fd_posllh, delimiter=",")
        self.init_csv_header()

    def init_csv_header(self):
        """Initializes the csv header for NAV-POSLLH."""
        self.writer.writerow(
            [
                "iTOW",
                "lon",
                "lat",
                "height",
                "hMSL",
                "undulation",
                "latE",
                "lonE",
                "heightE",
            ]
        )
        self.fd_posllh.flush()

    def decode_posllh(self, nav_posllh: UBXMessage) -> None:
        """Decodes the NAV-POSLLH message and writes the data to the csv file.

        Args:
            nav_posllh (UBXMessage): NAV-POSLLH parsed UBXMessage object
        """
        essential_attrs = [
            "iTOW",
            "lon",
            "lat",
            "height",
            "hMSL",
            "undulation",
            "latE",
            "lonE",
            "heightE",
        ]

        # Check if all essential attributes are present
        if not all(hasattr(nav_posllh, attr) for attr in essential_attrs):
            missing_attrs = [
                attr for attr in essential_attrs if not hasattr(nav_posllh, attr)
            ]
            self.logger.error(
                f"Missing essential attributes in NAV-POSLLH message: {', '.join(missing_attrs)}"
            )
            return

        # Extract values from the NAV-POSLLH message
        # row_data = [
        #     nav_posllh.iTOW,
        #     nav_posllh.lon,

        pass
