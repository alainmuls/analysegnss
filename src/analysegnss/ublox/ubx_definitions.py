from logging import Logger

# uBlox GNSS Identifiers mapping to standard single letters
UBLOX_GNSS_IDENTIFIER = {
    0: "G",  # GPS
    1: "S",  # SBAS
    2: "E",  # Galileo
    3: "C",  # BeiDou
    4: "I",  # IMES (Indoor Messaging System)
    5: "J",  # QZSS (Japanese Quasi-Zenith Satellite System)
    6: "R",  # GLONASS
}


def convert_ublox_gnss_identifier(gnss_id: int, logger: Logger = None) -> str:
    """Converts uBlox GNSS ID (numeric) to its standard single-letter identifier."""
    letter = UBLOX_GNSS_IDENTIFIER.get(gnss_id, "U")  # Default to 'U' for Unknown
    if letter == "U" and gnss_id not in UBLOX_GNSS_IDENTIFIER:
        log_message = f"Unknown uBlox gnssId: {gnss_id}. Returning 'U'."
        if logger:
            logger.warning(log_message)
    return letter


# Mapping for uBlox (gnssId, sigId) to frequency band and signal code
# Based on u-blox M8 Receiver Description, RXM-RAWX sigId table and general uBlox signal identifiers
UBLOX_SIGNAL_DETAILS = {
    # GPS (gnssId: 0)
    0: {
        0: {"freq_band": "L1", "signal_code": "C1"},  # L1C/A
        3: {"freq_band": "L2", "signal_code": "CL"},  # L2CL
        4: {"freq_band": "L2", "signal_code": "CM"},  # L2CM
        6: {"freq_band": "L5", "signal_code": "5I"},  # L5I
        7: {"freq_band": "L5", "signal_code": "5Q"},  # L5Q
    },
    # SBAS (gnssId: 1) - sigId is PRN
    1: {
        "DEFAULT": {"freq_band": "L1", "signal_code": "C1"},  # L1C/A for any SBAS PRN
    },
    # Galileo (gnssId: 2)
    2: {
        0: {"freq_band": "E1", "signal_code": "1C"},  # E1C
        1: {"freq_band": "E1", "signal_code": "1B"},  # E1B
        5: {"freq_band": "E5b", "signal_code": "5I"},  # E5bI
        6: {"freq_band": "E5b", "signal_code": "5Q"},  # E5bQ
        7: {"freq_band": "E5a", "signal_code": "5I"},  # E5aI
        8: {"freq_band": "E5a", "signal_code": "5Q"},  # E5aQ
    },
    # BeiDou (gnssId: 3)
    3: {
        0: {"freq_band": "B1I", "signal_code": "D1"},  # B1I (D1)
        1: {"freq_band": "B1I", "signal_code": "D2"},  # B1I (D2)
        2: {"freq_band": "B2I", "signal_code": "D1"},  # B2I (D1)
        3: {"freq_band": "B2I", "signal_code": "D2"},  # B2I (D2)
    },
    # IMES (gnssId: 4)
    4: {
        0: {"freq_band": "L1", "signal_code": "IMES"},
    },
    # QZSS (gnssId: 5)
    5: {
        0: {"freq_band": "L1", "signal_code": "C1"},  # L1C/A
        1: {"freq_band": "L1", "signal_code": "CD"},  # L1C (Data)
        2: {"freq_band": "L1", "signal_code": "CP"},  # L1C (Pilot)
        4: {"freq_band": "L2", "signal_code": "CM"},  # L2CM
        5: {"freq_band": "L2", "signal_code": "CL"},  # L2CL
        6: {"freq_band": "L5", "signal_code": "5I"},  # L5I
        7: {"freq_band": "L5", "signal_code": "5Q"},  # L5Q
    },
    # GLONASS (gnssId: 6)
    6: {
        0: {"freq_band": "G1", "signal_code": "1C"},  # L1OF (G1 C/A)
        2: {"freq_band": "G2", "signal_code": "2P"},  # L2OF (G2 C/A)
    },
}


def get_ublox_signal_details(
    gnss_id_num: int, sig_id: int | None, logger: Logger = None
) -> tuple[str, str]:
    """
    Derives frequency band and signal code from uBlox gnssId (numeric) and sigId.
    Returns ("N/A", "N/A") if not found or sig_id is None.
    """
    if sig_id is None:
        # This can happen if sigId is not present in the message for a measurement
        return "N/A", "N/A"

    gnss_signal_map = UBLOX_SIGNAL_DETAILS.get(gnss_id_num)
    if gnss_signal_map:
        signal_info = gnss_signal_map.get(
            sig_id, gnss_signal_map.get("DEFAULT")
        )  # Try specific sigId, then DEFAULT (for SBAS)
        if signal_info:
            return signal_info["freq_band"], signal_info["signal_code"]

    if logger:
        logger.warning(
            f"No signal details found for gnssId {gnss_id_num}, sigId {sig_id}. Returning 'N/A'."
        )
    return "N/A", "N/A"
