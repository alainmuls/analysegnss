import csv
import logging

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

        # Write the header line to the MGA-GPS-EPH csv file
        self.fd_eph = open(fn_eph, "w")
        self.writer = csv.writer(self.df_eph, delimiter=",")
        self.init_csv_header()

        self.dict_gps_nav = {
            "GNSS": [],
            "PRN": [],
            "TOW": [],
            "WNa": [],
            "URA": [],
            "SVHealth": [],
            "tgd": [],
            "IODC": [],
            "toc": [],
            "af0": [],
            "af1": [],
            "af2": [],
            "Crs": [],
            "DeltaN": [],
            "M0": [],
            "Cuc": [],
            "Cus": [],
            "eccen": [],
            "sqrtA": [],
            "Toe": [],
            "Cic": [],
            "Omega0": [],
            "Cis": [],
            "Crc": [],
            "i0": [],
            "omega": [],
            "OmegaDot": [],
            "IDOT": [],
        }

        self.init_csv_header()

        self.logger.info(f"{str_yellow('UBX_RXM_RAWX')} initialized")

    def init_csv_header(self):
        """initializes the csv header for UBX message MGA_GPS_EPH"""

        # write the header line to the UBX_RXM_RAWX csv file
        self.writer.writerow(self.dict_gps_nav.keys())
        self.fd_eph.flush()
