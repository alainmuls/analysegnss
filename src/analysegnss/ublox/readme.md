# u-blox UBX Message Parsers

This directory contains Python scripts designed to parse and process various u-blox UBX messages from binary files or streams. The primary goal is often to convert specific UBX message data into more accessible formats like CSV.

## Core Scripts

*   __`ubx_class.py`__:
    *   Defines the main `UBX` class which acts as an orchestrator for parsing UBX binary files.
    *   It uses `pyubx2` to read messages and dispatches them to specific handler classes (like `UBX_NAV_PVT`, `UBX_RXM_RAWX`, etc.) for detailed decoding and CSV output.
    *   Includes file validation and handling for different UBX message types.

*   __`ubx_parser.py`__:
    *   A command-line interface (CLI) script that utilizes the `UBX` class from `ubx_class.py`.
    *   It takes a UBX file as input and processes it to generate CSV files for the supported UBX messages.

*   __`ubx_definitions.py`__:
    *   Contains helper dictionaries and functions for interpreting u-blox specific codes.
    *   Includes mappings for GNSS identifiers (e.g., GPS, GLONASS, Galileo) and signal details (e.g., frequency band, signal code for RXM-RAWX).

## UBX Message Handler Classes

These scripts define classes, each responsible for decoding a specific UBX message type and typically writing its contents to a CSV file.

*   __`ubx_mga_gps_nav.py`__:
    *   Handles `UBX-MGA-GPS-EPH` (0x13 0x00) messages, specifically for GPS ephemeris data.
    *   Decodes ephemeris parameters and saves them to a CSV file.

*   __`ubx_nav_dop.py`__:
    *   Handles `UBX-NAV-DOP` (0x01 0x04) messages.
    *   Extracts Dilution of Precision (DOP) values (GDOP, PDOP, HDOP, VDOP, etc.) and writes them to a CSV.

*   __`ubx_nav_posllh.py`__:
    *   Handles `UBX-NAV-POSLLH` (0x01 0x02) messages.
    *   Decodes geodetic position (longitude, latitude, height, accuracy estimates) and saves to CSV.

*   __`ubx_nav_pvt.py`__:
    *   Handles `UBX-NAV-PVT` (0x01 0x07) messages (Position, Velocity, Time).
    *   Extracts a comprehensive set of navigation solution data (time, position, velocity, fix type, accuracy) and writes it to CSV.

*   __`ubx_nav_relposned.py`__:
    *   Handles `UBX-NAV-RELPOSNED` (0x01 0x3C) messages.
    *   Decodes relative positioning information in North-East-Down (NED) frame, typically used in RTK applications, and saves to CSV.

*   __`ubx_nav_sat.py`__:
    *   Handles `UBX-NAV-SAT` (0x01 0x35) messages.
    *   Extracts detailed information for each visible satellite (GNSS ID, SV ID, C/N0, elevation, azimuth, pseudorange residuals, flags) and writes one row per satellite observation to CSV.

*   __`ubx_rxm_rawx.py`__:
    *   Handles `UBX-RXM-RAWX` (0x02 0x15) messages.
    *   Decodes raw measurement data for each satellite signal (pseudorange, carrier phase, Doppler, C/N0, lock time) and writes to CSV.

## Examples and Test Scripts

*   __`ubx_nav_usage_example.py`__:
    *   Provides an example of how to use one of the message handler classes (`UBX_NAV_PVT` in this case) to parse a UBX file and generate a CSV.

*   __`ubx_serial_example.py`__:
    *   Demonstrates how to read and parse UBX messages (specifically `NAV-PVT`) directly from a serial port connection to a u-blox receiver using `pyubx2` and `pyserial`.

*   __`test_ubx_file.py`__:
    *   A simple script that uses `pyubx2.UBXReader` to read all messages from a UBX file and print their raw byte representation (hex) and parsed data structure.

*   __`test_ubx_rawx.py`__:
    *   Appears to be a test script focused on parsing `UBX-RXM-RAWX` messages, potentially also demonstrating the usage of the main `UBX` class from `ubx_class.py`.

