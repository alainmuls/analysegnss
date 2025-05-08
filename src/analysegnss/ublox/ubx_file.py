from pyubx2 import UBXReader, UBX_PROTOCOL
from rich import print as rprint

with open(
    "./data/ublox/2025-4-26_132532_serial-COM3_prise_statique_V1.ubx", "rb"
) as stream:
    ubr = UBXReader(stream, protfilter=UBX_PROTOCOL)
    for raw_data, parsed_data in ubr:
        # print(f"{raw_data}\n") # Original raw bytes, if you still want it
        hex_string = raw_data.hex()
        spaced_hex_string = " ".join(
            hex_string[i : i + 2] for i in range(0, len(hex_string), 2)
        )
        rprint(f"{spaced_hex_string} | {len(raw_data)} | {len(raw_data)-8} bytes\n")
        rprint(parsed_data.__dict__, f"| {parsed_data.__class__.__name__}")
        rprint(f"-" * 25)
