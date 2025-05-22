# Standard library imports
import datetime
import logging
import os
import struct  # Added for unpacking binary data
import sys
from dataclasses import dataclass, field

from pynmeagps import NMEAMessage
from pyrtcm import RTCMMessage
from pyubx2 import UBXMessage, UBXReader
from pyubx2.ubxtypes_core import UBX_CLASSES, ERR_IGNORE

from rich import print as rprint
from rich.status import Status

from analysegnss.ublox import ubx_rxm_rawx
from analysegnss.utils.utilities import str_green, str_red


from typing import Optional


@dataclass
class UBX:
    ubx_fn: Optional[str] = field(default=None)
    start_time: Optional[datetime.time] = field(default=None)
    end_time: Optional[datetime.time] = field(default=None)

    logger: Optional[logging.Logger] = field(default=None)
    _console_loglevel: int = field(default=logging.ERROR)

    # set classes for decoding uBlox messages to None
    ubx_rxm_rawx = None  # decoding of UBX-RXM-RAWX (0xB5 0x62)

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

    def parse_ubx_stream(self):
        """
        Parses the UBX file, identifies specific messages, and dispatches them
        to respective decoding classes.
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

        rich_status = Status("", spinner="aesthetic")
        rich_status.start()

        processed_messages_count = 0

        # for detecting which messages are in the UBX file
        ubx_msgs = []
        nmea_msgs = []
        rtcm_msgs = []
        with open(self.ubx_fn, "rb") as f_ubx:
            error_mode = ERR_IGNORE
            ubr = UBXReader(f_ubx, quitonerror=error_mode)

            for raw_msg, parsed_msg in ubr:
                if parsed_msg is not None:
                    # rprint(type(parsed_msg))
                    # rprint(type(raw_msg))
                    # Check if the message is a UBX message
                    if isinstance(parsed_msg, UBXMessage):
                        rich_status.update(
                            f"\rUBX message: [green]{parsed_msg.identity}[/green]"
                        )
                        # rprint(
                        #     f"parsed_msg.identity: {parsed_msg.identity} | {parsed_msg.msg_cls} | {parsed_msg.msg_id} | {parsed_msg.length}"
                        # )
                        if parsed_msg.identity not in ubx_msgs:
                            ubx_msgs.append(parsed_msg.identity)

                        match parsed_msg.identity:
                            case "MGA-GPS":
                                self._decode_mga_gps(payload=parsed_msg)
                            case "RXM-RAWX":
                                if self.ubx_rxm_rawx == None:  # station parameters
                                    self.ubx_rxm_rawx = ubx_rxm_rawx.UBX_RXM_RAWX(
                                        # fn_rawx="/tmp/ubx_rxm_rawx.csv"
                                    )

                                self.ubx_rxm_rawx.decode_rawx(rawx=parsed_msg)

                            # case "RXM-MEASX":
                            #     if self.logger:
                            #         self.logger.warning(
                            #             f"Unhandled UBX message type: {parsed_msg.identity} "
                            #             f"(0x{parsed_msg.msg_cls.hex()}, 0x{parsed_msg.msg_id.hex()})"
                            #             f", payload={parsed_msg.length}"
                            #         )

                            #         pass
                            case _:
                                # if self.logger:
                                #     self.logger.debug(
                                #         f"Unhandled message: {parsed_msg.identity} "
                                #     )
                                pass

                        # Increment the processed messages count
                        processed_messages_count += 1

                    elif isinstance(parsed_msg, NMEAMessage):
                        nmea_msg = parsed_msg.talker + parsed_msg.msgID
                        rich_status.update(f"\rNMEA message: [green]{nmea_msg}[/green]")
                        if nmea_msg not in nmea_msgs:
                            nmea_msgs.append(nmea_msg)

                    elif isinstance(parsed_msg, RTCMMessage):
                        rich_status.update(
                            f"RTCM message: [green]{parsed_msg.identity}[/green]"
                        )
                        rtcm_msg = parsed_msg.identity
                        if rtcm_msg not in rtcm_msgs:
                            rtcm_msgs.append(rtcm_msg)

                    else:
                        pass

        # end display of the spinner
        rich_status.stop()

        # get a sorted unique list of the ubx_msgs
        ubx_msgs = sorted(set(ubx_msgs))
        nmea_msgs = sorted(set(nmea_msgs))
        rtcm_msgs = sorted(set(rtcm_msgs))
        if self.logger:
            self.logger.info(
                f"UBX classes found in the file: {ubx_msgs} "
                f"({len(ubx_msgs)} unique classes)"
            )
            self.logger.info(
                f"NMEA classes found in the file: {nmea_msgs} "
                f"({len(nmea_msgs)} unique classes)"
            )
            self.logger.info(
                f"RTCM classes found in the file: {rtcm_msgs} "
                f"({len(rtcm_msgs)} unique classes)"
            )

        if self.logger:
            self.logger.info(
                str_green(
                    f"Finished parsing UBX stream from {self.ubx_fn}. "
                    f"Processed {processed_messages_count} targeted messages."
                )
            )
        rprint(
            f"Finished parsing UBX stream from [green]{self.ubx_fn}[/green]. "
            f"Processed [green]{processed_messages_count}[/green] targeted messages."
        )
