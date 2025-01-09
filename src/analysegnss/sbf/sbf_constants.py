# dict containing the PVT modes
DICT_SBF_PVTMODE = {
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
DICT_SBF_PVTERROR = {
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
LST_SBF_INTERVAL = [
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
