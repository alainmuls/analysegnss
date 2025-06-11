from pyubx2 import UBXMessage, UBXReader
from pyubx2.ubxtypes_core import UBX_CLASSES
from rich import print as rprint
from analysegnss.ublox.ubx_class import UBX


def parse_rawx_from_stream(byte_stream):
    """
    Parses UBX-RXM-RAWX messages from a byte stream.

    Args:
        byte_stream (bytes): A byte stream containing UBX messages.

    Yields:
        UBXMessage: A UBXMessage object representing a parsed UBX-RXM-RAWX message.
    """
    ubr = UBXReader(byte_stream)
    for raw_data, parsed_msg in ubr:
        # first_four_bytes_hex = " ".join(f"{b:02x}" for b in raw_data[0:4])
        # rprint(f"First 4 bytes (Preamble, Class, ID): {first_four_bytes_hex}")
        if (
            len(raw_data) >= 4
            and raw_data[0:2] == b"\xb5\x62"  # preamble
            and raw_data[2] == 2  # class
            and raw_data[3] == 21  # ID
        ):
            yield raw_data, parsed_msg


def parse_rawx_from_file(filename):
    """
    Parses UBX-RXM-RAWX messages from a UBX binary file.

    Args:
        filename (str): The path to the UBX binary file.

    Yields:
        UBXMessage: A UBXMessage object representing a parsed UBX-RXM-RAWX message.
    """
    with open(filename, "rb") as file:
        for msg in parse_rawx_from_stream(file):
            yield msg


# Example usage:
if __name__ == "__main__":
    # # Replace "ubx_bin.ubx" with the actual path to your file
    # for raw_data, parsed_data in parse_rawx_from_file(
    #     "./data/ublox/2025-4-26_132532_serial-COM3_prise_statique_V1.ubx"
    # ):
    #     # print(raw_data)
    #     hex_string = raw_data.hex()
    #     # spaced_hex_string = " ".join(
    #     #     hex_string[i : i + 2] for i in range(0, len(hex_string), 2)
    #     # )
    #     # rprint(f"{spaced_hex_string} | {len(raw_data)} | {len(raw_data)-8} bytes\n")
    #     message_identity_info = (
    #         f"UBX Message: {parsed_data.identity} "
    #         # f"(Class: 0x{parsed_data.msg_class[0]:02x}, ID: 0x{parsed_data.msg_id[0]:02x})"
    #     )

    #     # class_name_mnemonic = UBX_CLASSES.get(parsed_data.msg_class, "UNKNOWN_CLASS")
    #     # rprint(f"Class Name: {class_name_mnemonic}")
    #     rprint(
    #         f"Message: {message_identity_info}"
    #         f"  | Length: {len(raw_data)} bytes"
    #         f"  | Payload: {len(raw_data) - 8} bytes"
    #     )

    #     # rprint(parsed_data.__dict__)  # Print the dictionary on a new line for clarity
    #     # rprint(f"-" * 25)

    ubx = UBX(
        ubx_fn="./data/ublox/20250426_132532.ubx",
        start_time=None,
        end_time=None,
        logger=None,
    )
    ubx.validate_file()
    ubx.validate_start_time()
    ubx.validate_end_time()
