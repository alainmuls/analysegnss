"""
General PVT quality dictionary and conversion functions for different GNSS formats
"""

# General PVT quality dictionary that serves as a common reference
GENERAL_PVT_QUALITY_ID = {
    'INVALID': dict(desc="Invalid/No PVT available", color="red"),
    'STANDALONE': dict(desc="Stand-Alone PVT", color="cornflowerblue"),
    'DIFFERENTIAL': dict(desc="Differential PVT", color="darkcyan"),
    'SBAS': dict(desc="SBAS aided PVT", color="deepskyblue"),
    'SBAS_DFMC': dict(desc="SBAS Dual Frequency Multi Constellation", color="blue"),
    'RTK_FIXED': dict(desc="RTK with fixed ambiguities", color="green"),
    'RTK_FLOAT': dict(desc="RTK with float ambiguities", color="orange"),
    'PPP': dict(desc="Precise Point Positioning (PPP)", color="limegreen"),
    'RTK_MOVING_BASE_FIXED': dict(desc="Moving-base RTK with fixed ambiguities", color="goldenrod"),
    'RTK_MOVING_BASE_FLOAT': dict(desc="Moving-base RTK with float ambiguities", color="golden"),
    'FIXED_LOCATION': dict(desc="Fixed location", color="darkgreen"),
    'INS': dict(desc="INS Dead Reckoning", color="purple"),
    'MANUAL': dict(desc="Manual input mode", color="yellow"),
    'SIMULATION': dict(desc="Simulation mode", color="gray"),
}

def rtklib_to_general_quality(rtklib_mode: int) -> str:
    """Convert RTKLIB PVT mode to general quality identifier"""
    conversion = {
        1: 'RTK_FIXED',
        2: 'RTK_FLOAT',
        3: 'SBAS',
        4: 'DIFFERENTIAL',
        5: 'STANDALONE',
        6: 'PPP'
    }
    return conversion.get(rtklib_mode, 'INVALID')

def nmea_to_general_quality(nmea_quality: int) -> str:
    """Convert NMEA quality indicator to general quality identifier"""
    conversion = {
        0: 'INVALID',
        1: 'STANDALONE',
        2: 'DIFFERENTIAL',
        4: 'RTK_FIXED',
        5: 'RTK_FLOAT',  # Note: In NMEA this could also be PPP
        6: 'INS',
        7: 'MANUAL',
        8: 'SIMULATION'
    }
    return conversion.get(nmea_quality, 'INVALID')

def sbf_to_general_quality(sbf_mode: int) -> str:
    """Convert Septentrio SBF PVT mode to general quality identifier"""
    conversion = {
        0: 'INVALID',
        1: 'STANDALONE',
        2: 'DIFFERENTIAL',
        3: 'FIXED_LOCATION',
        4: 'RTK_FIXED',
        5: 'RTK_FLOAT',
        6: 'SBAS',
        7: 'RTK_MOVING_BASE_FIXED',
        8: 'RTK_MOVING_BASE_FLOAT',
        10: 'PPP',
        12: 'SIMULATION'
    }
    return conversion.get(sbf_mode, 'INVALID')

def glab_to_general_quality(glab_mode: int) -> str:
    """Convert GLAB PVT mode to general quality identifier"""
    conversion = {
        0: 'STANDALONE',
        1: 'PPP',
        5: 'SBAS',
        6: 'SBAS_DFMC',
        7: 'DIFFERENTIAL'
    }
    return conversion.get(glab_mode, 'INVALID')


def get_quality_info(general_quality: str) -> dict:
    """
    Get the description and color for a general quality identifier
    
    Args:
        general_quality: String identifier from the GENERAL_PVT_QUALITY dictionary
        
    Returns:
        Dictionary containing description and color for the quality level
    """
    return GENERAL_PVT_QUALITY_ID.get(general_quality, 
                                  dict(desc="Unknown", color="black"))
