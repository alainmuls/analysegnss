import math

# Constants and macros
SQR = lambda x: x * x
MU_GPS = 3.9860050e14
MU_GAL = 3.986004418e14
MU_CMP = 3.986004418e14
OMGE = 7.2921151467e-5
OMGE_GAL = 7.2921151467e-5
OMGE_CMP = 7.292115e-5
RTOL_KEPLER = 1e-14
MAX_ITER_KEPLER = 30
CLIGHT = 299792458.0
COS_5 = 0.9961946980917456
SIN_5 = -0.0871557427476582


def eph2pos(time, eph):
    rs = [0.0, 0.0, 0.0]
    dts = [0.0]
    var = [0.0]

    if eph["A"] <= 0.0:
        return rs, dts, var

    tk = time - eph["toe"]

    sys = eph["sys"]
    prn = eph["PRN"]

    if sys == "GAL":
        mu = MU_GAL
        omge = OMGE_GAL
    elif sys == "CMP":
        mu = MU_CMP
        omge = OMGE_CMP
    else:
        mu = MU_GPS
        omge = OMGE

    M = eph["M0"] + (math.sqrt(mu / (eph["A"] ** 3)) + eph["deln"]) * tk

    E = M
    for n in range(MAX_ITER_KEPLER):
        Ek = E
        E -= (E - eph["e"] * math.sin(E) - M) / (1.0 - eph["e"] * math.cos(E))
        if abs(E - Ek) < RTOL_KEPLER:
            break
    else:
        print(f"kepler iteration overflow sat={eph['sat']}")
        return rs, dts, var

    sinE = math.sin(E)
    cosE = math.cos(E)

    u = math.atan2(math.sqrt(1.0 - eph["e"] ** 2) * sinE, cosE - eph["e"]) + eph["omg"]
    r = eph["A"] * (1.0 - eph["e"] * cosE)
    i = eph["i0"] + eph["idot"] * tk
    sin2u = math.sin(2.0 * u)
    cos2u = math.cos(2.0 * u)
    u += eph["cus"] * sin2u + eph["cuc"] * cos2u
    r += eph["crs"] * sin2u + eph["crc"] * cos2u
    i += eph["cis"] * sin2u + eph["cic"] * cos2u
    x = r * math.cos(u)
    y = r * math.sin(u)
    cosi = math.cos(i)

    if sys == "CMP" and prn <= 5:
        O = eph["OMG0"] + eph["OMGd"] * tk - omge * eph["toes"]
        sinO = math.sin(O)
        cosO = math.cos(O)
        xg = x * cosO - y * cosi * sinO
        yg = x * sinO + y * cosi * cosO
        zg = y * math.sin(i)
        sino = math.sin(omge * tk)
        coso = math.cos(omge * tk)
        rs[0] = xg * coso + yg * sino * COS_5 + zg * sino * SIN_5
        rs[1] = -xg * sino + yg * coso * COS_5 + zg * coso * SIN_5
        rs[2] = -yg * SIN_5 + zg * COS_5
    else:
        O = eph["OMG0"] + (eph["OMGd"] - omge) * tk - omge * eph["toes"]
        sinO = math.sin(O)
        cosO = math.cos(O)
        rs[0] = x * cosO - y * cosi * sinO
        rs[1] = x * sinO + y * cosi * cosO
        rs[2] = y * math.sin(i)

    tk = time - eph["toc"]
    dts[0] = eph["f0"] + eph["f1"] * tk + eph["f2"] * tk * tk

    # Relativity correction
    dts[0] -= 2.0 * math.sqrt(mu * eph["A"]) * eph["e"] * sinE / (CLIGHT**2)

    # Position and clock error variance
    var[0] = var_uraeph(eph["sva"])

    return rs, dts, var
