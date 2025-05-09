# Standard library imports
import datetime
import logging
import os
import struct  # Added for unpacking binary data
import sys
from dataclasses import dataclass, field

from pyubx2 import UBXMessage, UBXReader
from pyubx2.ubxtypes_core import UBX_CLASSES
from rich import print as rprint

from analysegnss.utils.utilities import str_green, str_red


@dataclass
class UBX:
    ubx_fn: str = field(default=None)
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
        if not self.ubx_fn:
            if self.logger:
                self.logger.error("UBX filename (ubx_fn) cannot be None.")
            raise ValueError("UBX filename (ubx_fn) cannot be None.")

        if not os.path.isfile(self.ubx_fn):
            if self.logger:
                self.logger.error(f"File does not exist: {self.ubx_fn}")
            raise ValueError(f"File does not exist: {self.ubx_fn}")

        found_preamble = False
        preamble_position = -1
        preamble = b"\xb5\x62"
        preamble_len = len(preamble)

        try:
            with open(self.ubx_fn, "rb") as f:
                chunk_size = 4096  # Read 4KB at a time
                overlap = b""
                current_file_pos = 0  # Tracks the start position of the new data read in each iteration

                while True:
                    data_read = f.read(chunk_size)
                    # If no new data read and no overlap left, we're done
                    if not data_read and not overlap:
                        break

                    current_chunk = overlap + data_read

                    # This case should ideally not be hit if the loop condition above is correct
                    if not current_chunk:
                        break

                    idx = current_chunk.find(preamble)

                    if idx != -1:
                        found_preamble = True
                        # Calculate absolute position of preamble in the file
                        preamble_position = (current_file_pos - len(overlap)) + idx
                        break  # Found the first occurrence

                    # If EOF reached and preamble not found in the last processed chunk
                    if not data_read:
                        break

                    # Prepare overlap for the next iteration:
                    # These are the last (preamble_len - 1) bytes of the current_chunk
                    if (
                        len(current_chunk) >= preamble_len
                    ):  # Ensure current_chunk is long enough
                        overlap = current_chunk[-(preamble_len - 1) :]
                    else:  # current_chunk is shorter than preamble_len -1, so keep all of it
                        overlap = current_chunk

                    current_file_pos += len(data_read)
        except IOError as e:
            if self.logger:
                self.logger.error(f"Error opening or reading file {self.ubx_fn}: {e}")
            raise ValueError(f"Could not read file {self.ubx_fn}: {e}")

        if found_preamble:
            if self.logger:
                if preamble_position == 0:
                    self.logger.debug(
                        f"UBX preamble {preamble!r} found at the beginning of {self.ubx_fn}."
                    )
                else:
                    self.logger.info(
                        f"UBX preamble {preamble!r} found at offset {preamble_position} in {self.ubx_fn}. Data before this offset might be non-UBX."
                    )
                self.logger.debug(
                    f"File validation: UBX preamble presence confirmed in {self.ubx_fn}."
                )
        else:
            if self.logger:
                self.logger.warning(
                    f"UBX preamble {preamble!r} not found in {self.ubx_fn}. The file may not be a valid UBX stream or is corrupted."
                )
            # Depending on strictness, you might want to raise ValueError here.
            # Sticking to a warning if not found.

    def validate_start_time(self):
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
                    self.logger.debug(
                        f"Start time {self.start_time} validated successfully."
                    )
        else:
            if self.logger:
                self.logger.debug("No start time specified.")

    def validate_end_time(self):
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
                    self.logger.debug(
                        f"End time {self.end_time} validated successfully."
                    )
        else:
            if self.logger:
                self.logger.debug("No end time specified.")

    def validate_logger_level(self):
        if self.logger is not None:
            # get the logging level for the console
            for handler in self.logger.handlers:
                if isinstance(handler, logging.StreamHandler) and handler.stream in (
                    sys.stdout,
                    sys.stderr,
                ):
                    self._console_loglevel = handler.level
                    break  # Found one, no need to check others

            self.logger.debug(
                "Console log level set to "
                + f"{str_red(logging.getLevelName(self._console_loglevel))}"
            )

    def _calculate_ubx_checksum(self, message_bytes_for_checksum: bytes):
        """
        Calculates the UBX checksum (8-bit Fletcher Algorithm variant).
        The input bytes should include Class, ID, Length, and Payload.
        """
        ck_a = 0
        ck_b = 0
        for byte_val in message_bytes_for_checksum:
            ck_a = (ck_a + byte_val) & 0xFF
            ck_b = (ck_b + ck_a) & 0xFF
        return ck_a, ck_b

    def _decode_mga_gps(self, payload: bytes):
        """Placeholder for decoding UBX-MGA-GPS (0x13-0x00) payload."""
        if self.logger:
            self.logger.info(
                f"Decoding UBX-MGA-GPS (0x13-0x00), payload length: {len(payload)}"
            )
        # TODO: Implement actual decoding logic here
        pass

    def _decode_rxm_rawx(self, ubx_msg: bytes):
        """Placeholder for decoding UBX-RXM-RAWX (0x02-0x15) payload."""
        if self.logger:
            self.logger.info(
                f"Decoding UBX-RXM-RAWX (0x02-0x15), #SV: {ubx_msg.numMeas}"
            )
        # TODO: Implement actual decoding logic here

        pass

    # def parse_ubx_stream(self):
    #     """
    #     Parses the UBX file, identifies specific messages, and dispatches them
    #     to respective decoding functions.
    #     """
    #     if not self.ubx_fn:
    #         if self.logger:
    #             self.logger.error("UBX filename (ubx_fn) not set. Cannot parse.")
    #         return

    #     if self.logger:
    #         self.logger.info(f"Starting to parse UBX stream from {self.ubx_fn}")

    #     # UBX message constants
    #     PREAMBLE1 = 0xB5
    #     PREAMBLE2 = 0x62

    #     # Target messages (Class, ID)
    #     MSG_MGA_GPS = (0x13, 0x00)
    #     MSG_RXM_RAWX = (0x02, 0x15)  # UBX-RXM-RAWX

    #     processed_messages_count = 0
    #     skipped_bytes_count = 0

    #     try:
    #         with open(self.ubx_fn, "rb") as f:
    #             while True:
    #                 # --- 1. Search for Preamble ---
    #                 byte1_read = f.read(1)
    #                 if not byte1_read:
    #                     break  # End of File

    #                 if byte1_read[0] != PREAMBLE1:
    #                     skipped_bytes_count += 1
    #                     continue

    #                 byte2_read = f.read(1)
    #                 if not byte2_read:
    #                     break  # End of File

    #                 if byte2_read[0] != PREAMBLE2:
    #                     # Found 0xB5 but not 0x62, so re-evaluate the second byte read
    #                     f.seek(-1, os.SEEK_CUR)
    #                     skipped_bytes_count += 1
    #                     continue

    #                 # Preamble 0xB5 0x62 found
    #                 if skipped_bytes_count > 0 and self.logger:
    #                     self.logger.debug(
    #                         f"Skipped {skipped_bytes_count} bytes before finding UBX preamble at offset {f.tell()-2}"
    #                     )
    #                 skipped_bytes_count = 0

    #                 # --- 2. Read Header (Class, ID, Length) ---
    #                 header_data = f.read(4)  # Class (1), ID (1), Length (2)
    #                 if len(header_data) < 4:
    #                     if self.logger:
    #                         self.logger.warning(
    #                             "EOF reached while reading message header."
    #                         )
    #                     break

    #                 msg_class = header_data[0]
    #                 msg_id = header_data[1]
    #                 payload_len = struct.unpack("<H", header_data[2:4])[
    #                     0
    #                 ]  # Length is 2 bytes, little-endian

    #                 # --- 3. Read Payload ---
    #                 payload = f.read(payload_len)
    #                 if len(payload) < payload_len:
    #                     if self.logger:
    #                         self.logger.warning(
    #                             f"EOF reached reading payload for {msg_class:02X}-{msg_id:02X}. Expected {payload_len}, got {len(payload)}."
    #                         )
    #                     break

    #                 # --- 4. Read and Verify Checksum ---
    #                 checksum_bytes_read = f.read(2)
    #                 if len(checksum_bytes_read) < 2:
    #                     if self.logger:
    #                         self.logger.warning(
    #                             f"EOF reached reading checksum for {msg_class:02X}-{msg_id:02X}."
    #                         )
    #                     break

    #                 ck_a_recv, ck_b_recv = (
    #                     checksum_bytes_read[0],
    #                     checksum_bytes_read[1],
    #                 )

    #                 # Checksum is calculated over: Class, ID, Length_bytes, Payload
    #                 bytes_for_checksum = header_data + payload
    #                 ck_a_calc, ck_b_calc = self._calculate_ubx_checksum(
    #                     bytes_for_checksum
    #                 )

    #                 if ck_a_calc != ck_a_recv or ck_b_calc != ck_b_recv:
    #                     if self.logger:
    #                         self.logger.warning(
    #                             f"Checksum mismatch for {msg_class:02X}-{msg_id:02X} at offset {f.tell()-(6+payload_len)}. "
    #                             f"Recv: {ck_a_recv:02X}{ck_b_recv:02X}, Calc: {ck_a_calc:02X}{ck_b_calc:02X}. Skipping."
    #                         )
    #                     continue  # Continue to search for next preamble

    #                 # --- 5. Dispatch to Decoder ---
    #                 current_message_type = (msg_class, msg_id)
    #                 # if self.logger:
    #                 #     self.logger.debug(
    #                 #         f"Valid UBX message: Class=0x{msg_class:02X}, ID=0x{msg_id:02X}, Length={payload_len}"
    #                 #     )

    #                 if current_message_type == MSG_MGA_GPS:
    #                     self._decode_mga_gps(payload)
    #                 elif current_message_type == MSG_RXM_RAWX:
    #                     ubx_msg = (
    #                         byte1_read
    #                         + byte2_read
    #                         + header_data
    #                         + payload
    #                         + checksum_bytes_read
    #                     )
    #                     rprint(ubx_msg.hex())
    #                     rprint(ubx_msg.identity)
    #                     self._decode_rxm_rawx(payload)
    #                 else:
    #                     if self.logger:
    #                         self.logger.debug(
    #                             f"Unhandled UBX message type: Class=0x{msg_class:02X}, ID=0x{msg_id:02X}, Length={payload_len}"
    #                         )

    #                 # Increment the processed messages count
    #                 processed_messages_count += 1

    #     except FileNotFoundError:
    #         if self.logger:
    #             self.logger.error(f"File not found during parsing: {self.ubx_fn}")
    #     except Exception as e:
    #         if self.logger:
    #             self.logger.error(
    #                 f"An error occurred during UBX parsing: {e}", exc_info=True
    #             )

    #     if self.logger:
    #         self.logger.info(
    #             str_green(
    #                 f"Finished parsing UBX stream. Processed {processed_messages_count} "
    #                 f"targeted messages."
    #             )
    #         )

    def parse_ubx_stream(self):
        """
        Parses the UBX file, identifies specific messages, and dispatches them
        to respective decoding functions.
        """
        if not self.ubx_fn:
            if self.logger:
                self.logger.error("UBX filename (ubx_fn) not set. Cannot parse.")
            return

        if self.logger:
            self.logger.info(f"Starting to parse UBX stream from {self.ubx_fn}")

        # Target messages (Class, ID)
        MSG_MGA_GPS = (0x13, 0x00)  # UBX-MGA-GPS
        MSG_RXM_RAWX = (0x02, 0x15)  # UBX-RXM-RAWX

        processed_messages_count = 0

        with open(self.ubx_fn, "rb") as f_ubx:
            ubr = UBXReader(f_ubx)

            for raw_data, parsed_msg in ubr:
                msg_class = raw_data[2]
                msg_id = raw_data[3]
                # payload_len = struct.unpack("<H", raw_data[4:6])[
                #     0
                # ]  # Length is 2 bytes, little-endian
                current_message_type = (msg_class, msg_id)
                if current_message_type == MSG_MGA_GPS:
                    self._decode_mga_gps(parsed_msg)
                elif current_message_type == MSG_RXM_RAWX:
                    self._decode_rxm_rawx(parsed_msg)
                else:
                    if self.logger:
                        self.logger.debug(
                            f"Unhandled UBX message type: "
                            f"Class=0x{msg_class:02X}, ID=0x{msg_id:02X}"  # , Length={payload_len}"
                        )

                # Increment the processed messages count
                processed_messages_count += 1

        if self.logger:
            self.logger.info(
                str_green(
                    f"Finished parsing UBX stream. Processed {processed_messages_count} "
                    f"targeted messages."
                )
            )
