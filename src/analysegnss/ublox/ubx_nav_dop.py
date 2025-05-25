import csv
import logging

from pyubx2.ubxmessage import UBXMessage  # Import UBXMessage for type hinting
from analysegnss.utils.utilities import str_red


class UBX_NAV_DOP:
    """
    Class to handle the uBlox NAV-DOP message (0xB5 0x62)
    and writing of the data to a CSV file
    """

    def __init__(self, fn_dop: str = "/tmp/ubx_nav_dop.csv") -> None:
        """
        Initialize the UBX_NAV_DOP class.

        Args:
            fn_dop (str): Path to the CSV file where NAV-DOP data will be written.
        """

        self.logger = logging.getLogger("ubx_parser")

        # write the header line to the UBX_RXM_RAWX csv file
        self.df_dop = open(fn_dop, "w")
        self.writer = csv.writer(self.df_dop, delimiter=",")
        self.init_csv_header()

        # Initialize attributes to store the last written DOP values
        self.last_iTOW = None
        self.last_gdop = None
        self.last_pdop = None
        self.last_tdop = None
        self.last_vdop = None
        self.last_hdop = None
        self.last_ndop = None
        self.last_edop = None

    def init_csv_header(self):
        """initializes the csv header for RTCM message rxm_rawx"""
        # write the header line to the UBX_RXM_RAWX csv file
        self.writer.writerow(
            ["TOW", "GDOP", "PDOP", "TDOP", "VDOP", "HDOP", "NDOP", "EDOP"]
        )
        self.df_dop.flush()

    def decode_dop(self, nav_dop: UBXMessage) -> None:
        """decodes the NAV-DOP message and writes the data to the csv file

        Args:
            nav_dop (UBXMessage): NAV-DOP parsed UBXMessage object
        """
        essential_attrs = [
            "iTOW",
            "gDOP",
            "pDOP",
            "tDOP",
            "vDOP",
            "hDOP",
            "nDOP",
            "eDOP",
        ]
        missing_attrs = [attr for attr in essential_attrs if not hasattr(nav_dop, attr)]

        if missing_attrs:
            if self.logger:
                self.logger.error(
                    f"NAV-DOP message is missing essential attribute(s): "
                    f"{str_red(', '.join(missing_attrs))}. Cannot process."
                )
            return

        # Attributes are guaranteed to exist at this point by the check above
        iTOW = nav_dop.iTOW
        gdop = nav_dop.gDOP
        pdop = nav_dop.pDOP
        tdop = nav_dop.tDOP
        vdop = nav_dop.vDOP
        hdop = nav_dop.hDOP
        ndop = nav_dop.nDOP
        edop = nav_dop.eDOP

        # Check if any DOP value has changed or if it's the first set of values
        # self.last_iTOW is None indicates the first valid message to be processed.
        is_first_message_to_log = self.last_iTOW is None

        # Condition to write new data: either it's the first message or DOP values have changed.
        log_new_data = (
            is_first_message_to_log
            or gdop != self.last_gdop
            or pdop != self.last_pdop
            or tdop != self.last_tdop
            or vdop != self.last_vdop
            or hdop != self.last_hdop
            or ndop != self.last_ndop
            or edop != self.last_edop
        )

        if log_new_data:
            # If it's not the first message and DOP values have changed,
            # write the *previous* state before writing the new one.
            if not is_first_message_to_log:
                self.writer.writerow(
                    [
                        self.last_iTOW,
                        self.last_gdop,
                        self.last_pdop,
                        self.last_tdop,
                        self.last_vdop,
                        self.last_hdop,
                        self.last_ndop,
                        self.last_edop,
                    ]
                )

            # Write the data row to the CSV file
            self.writer.writerow([iTOW, gdop, pdop, tdop, vdop, hdop, ndop, edop])
            self.df_dop.flush()

            # Update the last known DOP values
            self.last_iTOW = iTOW
            self.last_gdop = gdop
            self.last_pdop = pdop
            self.last_tdop = tdop
            self.last_vdop = vdop
            self.last_hdop = hdop
            self.last_ndop = ndop
            self.last_edop = edop

        self.last_iTOW = iTOW  # Update last_iTOW to the current iTOW
