from pyubx2 import UBXReader, UBX_PROTOCOL

with open(
    "./data/ublox/2025-4-26_132532_serial-COM3_prise_statique_V1.ubx", "rb"
) as stream:
    ubr = UBXReader(stream, protfilter=UBX_PROTOCOL)
    for raw_data, parsed_data in ubr:
        print(parsed_data)
        input("press a key")
