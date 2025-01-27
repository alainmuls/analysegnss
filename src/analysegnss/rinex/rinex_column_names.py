# Define navigation column names for different GNSS systems
"""
Descriptions for the column names in the GPS navigation message.

This dictionary maps the column names to their corresponding descriptions for the
GPS navigation message. The keys are the column names, and the values are
the descriptions.
"""
gps_nav_col_descriptions = (
    ("af0", "Clock Bias"),
    ("af1", "Clock Drift"),
    ("af2", "Clock Drift Rate"),
    ("IODE", "Issue of Data Ephemeris"),
    ("Crs", "Amplitude of Sine Harmonic Correction Term to Orbit Radius"),
    ("delta_N", "Mean Motion Difference"),
    ("M0", "Mean Anomaly at Reference Time"),
    ("Cuc", "Amplitude of Cosine Harmonic Correction Term to Argument of Latitude"),
    ("eccen", "Eccentricity"),
    ("Cus", "Amplitude of Sine Harmonic Correction Term to Argument of Latitude"),
    ("sqrt_A", "Square Root of Semi-Major Axis"),
    ("toe", "Reference Time Ephemeris"),
    ("Cic", "Amplitude of Cosine Harmonic Correction Term to Angle of Inclination"),
    ("OMEGA_0", "Longitude of Ascending Node at Weekly Epoch"),
    ("Cis", "Amplitude of Sine Harmonic Correction Term to Angle of Inclination"),
    ("i0", "Inclination Angle at Reference Time"),
    ("Crc", "Amplitude of Cosine Harmonic Correction Term to Orbit Radius"),
    ("omega", "Argument of Perigee"),
    ("OMEGA_DOT", "Rate of Right Ascension"),
    ("IDOT", "Rate of Inclination Angle"),
    ("CodesL2", "Codes on L2 Channel"),
    ("WN", "GPS Week Number"),
    ("L2Pflag", "L2 P-code Data Flag"),
    ("SVacc", "SV Accuracy (URA Index)"),
    ("health", "SV Health"),
    ("TGD", "Group Delay Differential"),
    ("IODC", "Issue of Data Clock"),
    ("toc", "Clock Data Reference Time"),
    ("Fit", "Curve Fit Interval"),
    ("Spare_1", "Reserved Spare 1"),
    ("Spare_2", "Reserved Spare 2"),
)

"""
Descriptions for the column names in the GLONASS navigation message.

This dictionary maps the column names to their corresponding descriptions for the
GLONASS navigation message. The keys are the column names, and the values are
the descriptions.
"""
glonass_nav_col_descriptions = (
    ("TauN", "Satellite Clock Bias"),
    ("GammaN", "Relative Frequency Bias"),
    ("tk", "Message Frame Time"),
    ("X", "X coordinate of satellite position in PZ-90"),
    ("VX", "X component of satellite velocity in PZ-90"),
    ("AX", "X component of lunar-solar acceleration in PZ-90"),
    ("health", "Satellite Health Flag"),
    ("Y", "Y coordinate of satellite position in PZ-90"),
    ("VY", "Y component of satellite velocity in PZ-90"),
    ("AY", "Y component of lunar-solar acceleration in PZ-90"),
    ("freqNum", "Frequency Number"),
    ("Z", "Z coordinate of satellite position in PZ-90"),
    ("VZ", "Z component of satellite velocity in PZ-90"),
    ("AZ", "Z component of lunar-solar acceleration in PZ-90"),
    ("age", "Age of Operation Information"),
    ("Spare_1", "Reserved Spare 1"),
    ("Spare_2", "Reserved Spare 2"),
    ("Spare_3", "Reserved Spare 3"),
    ("Spare_4", "Reserved Spare 4"),
    # ("flags", "GLONASS Information Flags")
)

"""
Descriptions for the column names in the Galileo I/NAV navigation message.

This dictionary maps the column names to their corresponding descriptions for the
Galileo I/NAV navigation message. The keys are the column names, and the values are
the descriptions.
"""
galileo_inav_col_descriptions = (
    ("af0", "Clock bias"),
    ("af1", "Clock drift"),
    ("af2", "Clock drift rate"),
    ("IODE", "Issue of Data"),
    ("Crs", "Amplitude of sine correction to orbital radius"),
    ("delta_N", "Mean motion difference"),
    ("M0", "Mean anomaly at reference epoch"),
    ("Cuc", "Amplitude of cosine correction to argument of latitude"),
    ("eccen", "Eccentricity"),
    ("Cus", "Amplitude of sine correction to argument of latitude"),
    ("sqrt_A", "Square root of semi-major axis"),
    ("toe", "Time of Ephemeris"),
    ("Cic", "Amplitude of cosine correction to inclination"),
    ("OMEGA_0", "Longitude of ascending node"),
    ("Cis", "Amplitude of sine correction to inclination"),
    ("i0", "Inclination angle"),
    ("Crc", "Amplitude of cosine correction to orbital radius"),
    ("omega", "Argument of perigee"),
    ("OMEGA_DOT", "Rate of change of right ascension"),
    ("IDOT", "Rate of change of inclination"),
    ("INAV_source", "INAV Source"),
    ("WN", "Galileo System Time Week Number"),
    ("Spare_1", "Reserved Spare 1"),
    ("Version", "Navigation Message Version"),
    ("E1B_HS", "E1B Health Status"),
    ("BGD_E1E5a", "E1-E5a Broadcast Group Delay"),
    ("BGD_E1E5b", "E1-E5b Broadcast Group Delay"),
    ("GST_TOW", "Galileo System Time Time of Week"),
    ("SISA", "Signal in Spare Accuracy"),
    ("Spare_2", "Reserved Spare 2"),
    ("Spare_3", "Reserved Spare 3"),
)

"""
Descriptions for the column names in the Galileo F/NAV navigation message.

This dictionary maps the column names to their corresponding descriptions for the
Galileo F/NAV navigation message. The keys are the column names, and the values are
the descriptions.
"""
galileo_fnav_col_descriptions = (
    ("af0", "Satellite Clock Bias"),
    ("af1", "Satellite Clock Drift"),
    ("af2", "Satellite Clock Drift Rate"),
    ("IODnav", "Issue of Data Navigation"),
    ("Crs", "Amplitude of Sine Harmonic Correction Term to Orbit Radius"),
    ("delta_N", "Mean Motion Difference"),
    ("M0", "Mean Anomaly at Reference Time"),
    ("Cuc", "Amplitude of Cosine Harmonic Correction Term to Argument of Latitude"),
    ("eccen", "Eccentricity"),
    ("Cus", "Amplitude of Sine Harmonic Correction Term to Argument of Latitude"),
    ("sqrt_A", "Square Root of Semi-Major Axis"),
    ("toe", "Reference Time Ephemeris"),
    ("Cic", "Amplitude of Cosine Harmonic Correction Term to Angle of Inclination"),
    ("OMEGA_0", "Longitude of Ascending Node at Weekly Epoch"),
    ("Cis", "Amplitude of Sine Harmonic Correction Term to Angle of Inclination"),
    ("i0", "Inclination Angle at Reference Time"),
    ("Crc", "Amplitude of Cosine Harmonic Correction Term to Orbit Radius"),
    ("omega", "Argument of Perigee"),
    ("OMEGA_DOT", "Rate of Right Ascension"),
    ("IDOT", "Rate of Inclination Angle"),
    # Additional gfzrnx columns in correct order
    ("FNAV_source", "Data Source"),
    ("WN", "Galileo System Time Week Number"),
    ("Spare_1", "Reserved Spare 1"),
    ("Version", "Navigation Message Version"),
    ("E5ahs", "E5a Signal Health Status"),
    ("BGD_E1E5a", "E1-E5a Group Delay Differential"),
    ("DVS", "Data Validity Status"),
    ("GST_TOW", "Galileo System Time Time of Week"),
    ("SISA", "Signal in Spare Accuracy"),
    ("Spare_2", "Reserved Spare 2"),
    ("Spare_3", "Reserved Spare 3"),
)

"""
Descriptions for the column names in the Beidou D1 navigation message.

This dictionary maps the column names to their corresponding descriptions for the
Beidou D1 navigation message. The keys are the column names, and the values are
the descriptions.
"""
beidou_d1_nav_col_descriptions = (
    ("af0", "Satellite Clock Offset"),
    ("af1", "Satellite Clock Drift"),
    ("af2", "Satellite Clock Drift Rate"),
    ("IODE", "Age of Data Ephemeris"),
    ("Crs", "Amplitude of Sine Harmonic Correction Term to Orbit Radius"),
    ("delta_N", "Mean Motion Difference"),
    ("M0", "Mean Anomaly at Reference Time"),
    ("Cuc", "Amplitude of Cosine Harmonic Correction Term to Argument of Latitude"),
    ("eccen", "Eccentricity"),
    ("Cus", "Amplitude of Sine Harmonic Correction Term to Argument of Latitude"),
    ("sqrt_A", "Square Root of Semi-Major Axis"),
    ("toe", "Reference Time Ephemeris"),
    ("Cic", "Amplitude of Cosine Harmonic Correction Term to Angle of Inclination"),
    ("OMEGA_0", "Longitude of Ascending Node at Weekly Epoch"),
    ("Cis", "Amplitude of Sine Harmonic Correction Term to Angle of Inclination"),
    ("i0", "Inclination Angle at Reference Time"),
    ("Crc", "Amplitude of Cosine Harmonic Correction Term to Orbit Radius"),
    ("omega", "Argument of Perigee"),
    ("OMEGA_DOT", "Rate of Right Ascension"),
    ("IDOT", "Rate of Inclination Angle"),
    ("Spare_1", "Reserved Spare 1"),
    ("BDS_WN", "Beidou System Time Week Number"),
    ("Spare_2", "Reserved Spare 2"),
    ("SVacc", "Satellite Accuracy"),
    ("SatH1", "Autonomous Satellite Health Flag"),
    ("TGD1", "B1/B3 Group Delay Differential"),
    ("TGD2", "B2/B3 Group Delay Differential"),
    ("toc", "Clock Data Reference Time"),
    ("AODC", "Age of Data Clock"),
    ("Spare_3", "Reserved Spare 3"),
    ("Spare_4", "Reserved Spare 4"),
)

"""
Descriptions for the column names in the Beidou D2 navigation message.

This dictionary maps the column names to their corresponding descriptions for the
Beidou D2 navigation message. The keys are the column names, and the values are
the descriptions.
"""
beidou_d2_nav_col_descriptions = beidou_d1_nav_col_descriptions


nav_message_descriptions = {
    ("G", "LNAV"): gps_nav_col_descriptions,
    ("R", "FDMA"): glonass_nav_col_descriptions,
    ("E", "INAV"): galileo_inav_col_descriptions,
    ("E", "FNAV"): galileo_fnav_col_descriptions,
    ("C", "D1"): beidou_d1_nav_col_descriptions,
    ("C", "D2"): beidou_d2_nav_col_descriptions,
}


# Usage example:
def get_nav_description(gnss_type: str, nav_type: str) -> tuple:
    return nav_message_descriptions.get((gnss_type, nav_type))


def get_nav_param_names(gnss: str, nav_type: str) -> str:
    """Get comma-separated string of navigation parameter names for given GNSS and nav type

    Args:
        gnss: GNSS system identifier (G/R/E/C)
        nav_type: Navigation message type (LNAV/INAV/FNAV/D1/D2)

    Returns:
        Comma-separated string of parameter names
    """
    nav_desc = get_nav_description(gnss, nav_type)
    return ",".join(param[0] for param in nav_desc)
