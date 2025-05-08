from pyubx2 import UBXReader, UBXMessage
from rich import print as rprint


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
    # Replace "ubx_bin.ubx" with the actual path to your file
    for raw_data, parsed_data in parse_rawx_from_file(
        "./data/ublox/2025-4-26_132532_serial-COM3_prise_statique_V1.ubx"
    ):
        # print(raw_data)
        hex_string = raw_data.hex()
        # spaced_hex_string = " ".join(
        #     hex_string[i : i + 2] for i in range(0, len(hex_string), 2)
        # )
        # rprint(f"{spaced_hex_string} | {len(raw_data)} | {len(raw_data)-8} bytes\n")
        rprint(parsed_data.__dict__, f"| {parsed_data.__class__.__name__}")
        rprint(f"-" * 25)
