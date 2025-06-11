import csv
import logging
from pyubx2.ubxmessage import UBXMessage  # For type hinting

# Assuming str_yellow is available in your project utils
# If not, you can remove its usage or define a simple version
from analysegnss.utils.utilities import str_yellow


class UBX_NAV_RELPOSNED:
    """
    Manages the decoding of uBlox UBX-NAV-RELPOSNED messages (0x01 0x3C)
    and writing of the data to a CSV file.
    """

    def __init__(self, fn_relposned: str = "/tmp/ubx_nav_relposned.csv") -> None:
        """
        Initializes an instance of UBX_NAV_RELPOSNED.

        Args:
            fn_relposned (str): The path to the CSV file where NAV-RELPOSNED data will be stored.
        """
        self.logger = logging.getLogger("ubx_parser")

        # Fields from NAV-RELPOSNED to extract.
        # pyubx2 handles scaling for heading (e.g., 1e-5 deg to deg) automatically.
        self.relposned_fields = [
            "version",
            "refStationId",
            "iTOW",
            "relPosN",  # cm
            "relPosE",  # cm
            "relPosD",  # cm
            "relPosLength",  # cm
            "relPosHeading",  # deg (scaled by 1e-5, pyubx2 handles this)
            "relPosHPN",  # 0.1 mm
            "relPosHPE",  # 0.1 mm
            "relPosHPD",  # 0.1 mm
            "relPosHPLength",  # 0.1 mm
            "accN",  # 0.1 mm
            "accE",  # 0.1 mm
            "accD",  # 0.1 mm
            "accLength",  # 0.1 mm
            "accHeading",  # deg (scaled by 1e-5, pyubx2 handles this)
            "flags",
        ]

        # Fields in cm that need to be converted to meters (divide by 100)
        self.fields_cm_to_m = {
            "relPosN",
            "relPosE",
            "relPosD",
            "relPosLength",
        }

        # Fields in 0.1mm that need to be converted to meters (divide by 10000)
        self.fields_0_1mm_to_m = {
            "relPosHPN",
            "relPosHPE",
            "relPosHPD",
            "relPosHPLength",
            "accN",
            "accE",
            "accD",
            "accLength",
        }

        self.fn_relposned = fn_relposned
        try:
            # Use newline='' to prevent blank rows in CSV on Windows
            self.fd_relposned = open(self.fn_relposned, "w", newline="")
            self.writer = csv.writer(self.fd_relposned, delimiter=",")
            self.init_csv_header()
            self.logger.info(
                f"{str_yellow('UBX_NAV_RELPOSNED')} initialized, writing to {self.fn_relposned}"
            )
        except IOError as e:
            self.logger.error(
                f"Failed to open file {self.fn_relposned} for UBX_NAV_RELPOSNED: {e}"
            )
            # To prevent further errors, ensure writer is not used if file opening failed
            self.writer = None  # type: ignore
            self.fd_relposned = None  # type: ignore
            raise  # Re-raise the exception so the caller is aware

    def init_csv_header(self) -> None:
        """Initializes the CSV header for NAV-RELPOSNED data."""
        if self.writer and self.fd_relposned:
            self.writer.writerow(self.relposned_fields)
            self.fd_relposned.flush()

    def decode_relposned(self, relposned_msg: UBXMessage) -> None:
        """
        Decodes a UBX-NAV-RELPOSNED message and writes its data to the CSV file.

        Args:
            relposned_msg (UBXMessage): A parsed UBX-NAV-RELPOSNED message object.
        """
        if not self.writer:
            self.logger.error(
                "CSV writer not initialized for NAV-RELPOSNED. Cannot write data."
            )
            return

        if relposned_msg.identity != "NAV-RELPOSNED":
            self.logger.warning(
                f"Attempted to decode a non NAV-RELPOSNED message ({relposned_msg.identity}) with decode_relposned."
            )
            return

        row_data = []
        for field in self.relposned_fields:
            value = getattr(relposned_msg, field, None)
            if value is not None:
                if field in self.fields_cm_to_m:
                    row_data.append(value / 100.0)  # cm to m
                elif field in self.fields_0_1mm_to_m:
                    row_data.append(value / 10000.0)  # 0.1mm to m
                else:
                    row_data.append(value)
            else:
                row_data.append(None)  # Append None or an empty string ''

        self.writer.writerow(row_data)
        if self.fd_relposned:
            self.fd_relposned.flush()

    def close(self) -> None:
        """Closes the CSV file."""
        if self.fd_relposned and not self.fd_relposned.closed:
            self.fd_relposned.close()
            self.logger.info(
                f"UBX_NAV_RELPOSNED CSV file '{self.fn_relposned}' closed."
            )

    def __del__(self) -> None:
        """Ensures the file is closed when the object is garbage collected."""
        try:
            if (
                hasattr(self, "fd_relposned")
                and self.fd_relposned
                and not self.fd_relposned.closed
            ):
                self.fd_relposned.close()
        except Exception:
            # Suppress exceptions in __del__ as logger might not be available
            pass
