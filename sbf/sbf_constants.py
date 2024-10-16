# dict containing the PVT modes
dict_sbf_pvtmode = {
    0: dict(desc="No PVT available", color="black"),
    1: dict(desc="Stand-Alone PVT", color="cornflowerblue"),
    2: dict(desc="Differential PVT", color="darkcyan"),
    3: dict(desc="Fixed location", color="drakgreen"),
    4: dict(desc="RTK with ﬁxed ambiguities", color="green"),
    5: dict(desc="RTK with ﬂoat ambiguities", color="orange"),
    6: dict(desc="SBAS aided PVT", color="deepskyblue"),
    7: dict(desc="moving-base RTK with ﬁxed ambiguities", color="goldenrod"),
    8: dict(desc="moving-base RTK with ﬂoat ambiguities", color="golden"),
    10: dict(desc="Precise Point Positioning (PPP)", color="limegreen"),
    12: dict(desc="Reserved", color="gray"),
}

# dict containing the PVT errors
dict_sbf_pvterror = {
    0: "No Error",
    1: "Not enough measurements",
    2: "Not enough ephemerides available",
    3: "DOP too large (larger than 15)",
    4: "Sum of squared residuals too large",
    5: "No convergence",
    6: "Not enough measurements after outlier rejection",
    7: "Position output prohibited due to export laws",
    8: "Not enough differential corrections available",
    9: "Base station coordinates unavailable",
    10: "Ambiguities not ﬁxed and user requested to only output RTK-ﬁxed positions",
}

# list with intervals for outputting SBF messages
lst_sbf_interval = [
    0.01,
    0.02,
    0.04,
    0.05,
    0.1,
    0.2,
    0.5,
    1,
    2,
    5,
    10,
    15,
    30,
    60,
    120,
    300,
    1800,
    3600,
]


def closest(lst: list, value: float):
    """
    closest find the closest element in the given list
    """
    return lst[min(range(len(lst)), key=lambda i: abs(lst[i] - value))]


dict_signal_types = {
    0: {"type": "L1CA", "gnss": "GPS", "freq": 1575.42e3, "code": "1C"},
    1: {"type": "L1P", "gnss": "GPS", "freq": 1575.42e3, "code": "1W"},
    2: {"type": "L2P", "gnss": "GPS", "freq": 1227.60e3, "code": "2W"},
    3: {"type": "L2C", "gnss": "GPS", "freq": 1227.60e3, "code": "2L"},
    4: {"type": "L5", "gnss": "GPS", "freq": 1176.45e3, "code": "5Q"},
    5: {"type": "L1C", "gnss": "GPS", "freq": 1575.42e3, "code": "1L"},
    6: {"type": "L1CA", "gnss": "QZSS", "freq": 1575.42e3, "code": "1C"},
    7: {"type": "L2C", "gnss": "QZSS", "freq": 1227.60e3, "code": "2L"},
    8: {
        "type": "L1CA",
        "gnss": "GLONASS",
        "freq": "1602.00E3+(FreqNr-8)*9/16",
        "code": "1C",
    },
    9: {
        "type": "L1P",
        "gnss": "GLONASS",
        "freq": "1602.00E3+(FreqNr-8)*9/16",
        "code": "1P",
    },
    10: {
        "type": "L2P",
        "gnss": "GLONASS",
        "freq": "1246.00E3+(FreqNr-8)*7/16",
        "code": "2P",
    },
    11: {
        "type": "L2CA",
        "gnss": "GLONASS",
        "freq": "1246.00E3+(FreqNr-8)*7/16",
        "code": "2C",
    },
    12: {"type": "L3", "gnss": "GLONASS", "freq": 1202.025e3, "code": "3Q"},
    13: {"type": "B1C", "gnss": "BeiDou", "freq": 1575.42e3, "code": "1P"},
    14: {"type": "B2a", "gnss": "BeiDou", "freq": 1176.45e3, "code": "5P"},
    15: {"type": "L5", "gnss": "NavIC/IRNSS", "freq": 1176.45e3, "code": "5A"},
    17: {"type": "E1 (L1BC)", "gnss": "Galileo", "freq": 1575.42e3, "code": "1C"},
    19: {"type": "E3 (E3BC)", "gnss": "Galileo", "freq": 1278.75e3, "code": "6C"},
    20: {"type": "E5a", "gnss": "Galileo", "freq": 1176.45e3, "code": "5Q"},
    21: {"type": "E5b", "gnss": "Galileo", "freq": 1207.14e3, "code": "7Q"},
    22: {"type": "E5 AltBoc", "gnss": "Galileo", "freq": 1191.795e3, "code": "8Q"},
    23: {"type": "LBand", "gnss": "MSS", "freq": "L-bandE3 beam speciﬁc", "code": "NA"},
    24: {"type": "L1CA", "gnss": "SBAS", "freq": 1575.42e3, "code": "1C"},
    25: {"type": "L5", "gnss": "SBAS", "freq": 1176.45e3, "code": "5I"},
    26: {"type": "L5", "gnss": "QZSS", "freq": 1176.45e3, "code": "5Q"},
    27: {"type": "L6", "gnss": "QZSS", "freq": 1278.7528e3, "code": ""},
    28: {"type": "B1I", "gnss": "BeiDou", "freq": 1561.098e3, "code": "2I"},
    29: {"type": "B2I", "gnss": "BeiDou", "freq": 1207.14e3, "code": "7I"},
    30: {"type": "B3I", "gnss": "BeiDou", "freq": 1268.52e3, "code": "6I"},
    32: {"type": "L1C", "gnss": "QZSS", "freq": 1575.42e3, "code": "1L"},
    33: {"type": "L1S", "gnss": "QZSS", "freq": 1575.42e3, "code": "1Z"},
    34: {"type": "B2b", "gnss": "BeiDou", "freq": 1207.14e3, "code": "7D"},
}


def ssn_prn2str(prn: int) -> str:
    """
    Converts the Septentrio PRN numbering to representation such as 'E19' or 'G07'

    Arguments:
        prn: Septentrio PRN number

    Returns:
        returns PRN number like 'E19' or 'G09'
    """
    try:
        if (prn >= 1) & (prn <= 37):
            return f"G{prn:02.0f}"
        elif (prn >= 38) & (prn <= 61):
            return f"R{prn - 37:02.0f}"
        elif (prn >= 71) & (prn <= 106):
            return f"E{prn - 70:02.0f}"
        elif (prn >= 141) & (prn <= 180):
            return f"B{prn - 140:02.0f}"
        elif (prn >= 120) & (prn <= 138):
            return f"S{prn:03.0f}"
        else:
            return f"X{prn:03.0f}"
    except TypeError:
        return prn


def ssnerr_prn2str(prn: str) -> str:
    """
    Converts the Septentrio PRN numbering to representation such as 'E19' or 'G07'

    Arguments:
        prn: Septentrio PRN number

    Returns:
        returns PRN number like 'E19' or 'G09'
    """
    try:
        iprn = int(prn)
        if (iprn >= 1) & (iprn <= 37):
            return f"G{iprn:02.0f}"
        elif (iprn >= 38) & (iprn <= 61):
            return f"R{iprn - 37:02.0f}"
        elif (iprn >= 71) & (iprn <= 106):
            return f"E{iprn - 70:02.0f}"
        elif (iprn >= 141) & (iprn <= 180):
            return f"B{iprn - 140:02.0f}"
        elif (iprn >= 120) & (iprn <= 138):
            return f"S{iprn:03.0f}"
        else:
            return f"X{iprn:03.0f}"
    except ValueError:
        return prn
