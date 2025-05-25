import csv
import logging
from pyubx2.ubxmessage import UBXMessage  # For type hinting

# Assuming str_yellow is available in your project utils
# If not, you can remove its usage or define a simple version
from analysegnss.utils.utilities import str_yellow
from analysegnss.ublox.ubx_definitions import (
    convert_ublox_gnss_identifier,
    get_ublox_signal_details,
)


class UBX_NAV_PVT:
    """
    Manages the decoding of uBlox UBX-NAV-PVT messages (0xB5 0x62 0x01 0x07)
    and writing of the data to a CSV file.
    """

    def __init__(self, fn_nav_pvt: str = "/tmp/ubx_nav_pvt.csv") -> None:
        """
        Initializes an instance of UBX_NAV_PVT.

        Args:
            fn_nav_pvt (str): The path to the CSV file where NAV-PVT data will be stored.
        """
        self.logger = logging.getLogger("ubx_parser")

        # These are the fields we'll extract from NAV-PVT and write to CSV
        # They correspond to attributes of the pyubx2 parsed NAV-PVT message
        self.pvt_fields = [
            "iTOW",
            "year",
            "month",
            "day",
            "hour",
            "min",
            "sec",
            "valid",
            "tAcc",
            "nano",
            "fixType",
            "flags",
            "flags2",
            "numSV",
            "lon",
            "lat",
            "height",
            "hMSL",
            "hAcc",
            "vAcc",
            "velN",
            "velE",
            "velD",
            "gSpeed",
            "headMot",
            "sAcc",
            "headAcc",
            "pDOP",
            # These fields might not be present in all NAV-PVT message versions
            # getattr in decode_pvt will handle missing attributes gracefully
            "headVeh",
            "magDec",
            "magAcc",
        ]

        self.fn_nav_pvt = fn_nav_pvt
        self.fd_pvt = open(self.fn_nav_pvt, "w")
        self.writer = csv.writer(self.fd_pvt, delimiter=",")
        self.init_csv_header()

        self.logger.info(
            f"{str_yellow('UBX_NAV_PVT')} initialized, writing to {self.fn_nav_pvt}"
        )

    def init_csv_header(self) -> None:
        """Initializes the CSV header for NAV-PVT data."""
        self.writer.writerow(self.pvt_fields)
        self.fd_pvt.flush()

    def decode_pvt(self, pvt_msg: UBXMessage) -> None:
        """
        Decodes a UBX-NAV-PVT message and writes its data to the CSV file.

        Args:
            pvt_msg (UBXMessage): A parsed UBX-NAV-PVT message object.
        """
        if pvt_msg.identity != "NAV-PVT":
            self.logger.warning(
                f"Attempted to decode a non NAV-PVT message ({pvt_msg.identity}) with decode_pvt."
            )
            return

        row_data = [getattr(pvt_msg, field, None) for field in self.pvt_fields]
        self.writer.writerow(row_data)
        self.fd_pvt.flush()

    def close(self) -> None:
        """Closes the CSV file."""
        if self.fd_pvt and not self.fd_pvt.closed:
            self.fd_pvt.close()
            self.logger.info(f"UBX_NAV_PVT CSV file '{self.fn_nav_pvt}' closed.")

    def __del__(self) -> None:
        """Ensures the file is closed when the object is garbage collected."""
        try:
            if hasattr(self, "fd_pvt") and self.fd_pvt and not self.fd_pvt.closed:
                self.fd_pvt.close()
        except Exception:
            # It's generally good practice to suppress exceptions in __del__
            pass
