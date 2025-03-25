"""
General PNT quality dictionary and conversion functions for different GNSS formats
"""

# General PNT quality dictionary that serves as a common reference
STANDARD_PNT_QUALITY_ID = {
    "INVALID": dict(desc="Invalid/No PNT available", color="red"),
    "STANDALONE": dict(desc="Stand-Alone PNT", color="cornflowerblue"),
    "DIFFERENTIAL": dict(desc="Differential PNT", color="darkcyan"),
    "SBAS": dict(desc="SBAS aided PNT", color="deepskyblue"),
    "SBAS_DFMC": dict(desc="SBAS Dual Frequency Multi Constellation", color="blue"),
    "RTK_FIXED": dict(desc="RTK with fixed ambiguities", color="green"),
    "RTK_FLOAT": dict(
        desc="RTK with float ambiguities (NMEA: RTK Float or PPP)", color="orange"
    ),
    "PPP": dict(desc="Precise Point Positioning (PPP)", color="limegreen"),
    "RTK_MOVING_BASE_FIXED": dict(
        desc="Moving-base RTK with fixed ambiguities", color="goldenrod"
    ),
    "RTK_MOVING_BASE_FLOAT": dict(
        desc="Moving-base RTK with float ambiguities", color="golden"
    ),
    "FIXED_LOCATION": dict(desc="Fixed location", color="darkgreen"),
    "INS": dict(desc="INS Dead Reckoning", color="purple"),
    "MANUAL": dict(desc="Manual input mode", color="black"),
    "SIMULATION": dict(desc="Simulation mode", color="gray"),
}


def rtklib_to_standard_pntqual(rtklib_mode: int) -> str:
    """Convert RTKLIB PNT mode to standard quality identifier"""
    conversion = {
        1: "RTK_FIXED",
        2: "RTK_FLOAT",
        3: "SBAS",
        4: "DIFFERENTIAL",
        5: "STANDALONE",
        6: "PPP",
    }
    return conversion.get(rtklib_mode, "INVALID")


def nmea_to_standard_pntqual(nmea_quality: int) -> str:
    """Convert NMEA quality indicator to general quality identifier"""
    conversion = {
        0: "INVALID",
        1: "STANDALONE",
        2: "DIFFERENTIAL",
        4: "RTK_FIXED",
        5: "RTK_FLOAT",  # Note: In NMEA this could also be PPP
        6: "INS",
        7: "MANUAL",
        8: "SIMULATION",
    }
    return conversion.get(nmea_quality, "INVALID")


def sbf_to_standard_pntqual(sbf_mode: int) -> str:
    """Convert Septentrio SBF PNT mode to general quality identifier"""
    conversion = {
        0: "INVALID",
        1: "STANDALONE",
        2: "DIFFERENTIAL",
        3: "FIXED_LOCATION",
        4: "RTK_FIXED",
        5: "RTK_FLOAT",
        6: "SBAS",
        7: "RTK_MOVING_BASE_FIXED",
        8: "RTK_MOVING_BASE_FLOAT",
        10: "PPP",
        12: "SIMULATION",
    }
    return conversion.get(sbf_mode, "INVALID")


def glab_to_standard_pntqual(glab_mode: int) -> str:
    """Convert GLAB PNT mode to general quality identifier"""
    conversion = {
        0: "STANDALONE",
        1: "PPP",
        5: "SBAS",
        6: "SBAS_DFMC",
        7: "DIFFERENTIAL",
    }
    return conversion.get(glab_mode, "INVALID")


def get_pntquality_info(standard_quality: str) -> dict:
    """
    Get the description and color for a standard quality identifier

    Args:
        standard_quality: String identifier from the STANDARD_PNT_QUALITY_ID dictionary

    Returns:
        Dictionary containing description and color for the quality level
    """
    return STANDARD_PNT_QUALITY_ID.get(
        standard_quality, dict(desc="Unknown", color="black")
    )
