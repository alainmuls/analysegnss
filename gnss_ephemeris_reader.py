import csv

import numpy as np

from src.analysegnss.gnss.GNSSephemeris import GNSSEphemeris


def read_nav_csv(csv_file):
    ephemerides = []

    with open(csv_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            eph = GNSSEphemeris()

            # Time parameters
            eph.toe = int(float(row["toe"]))
            try:
                eph.toc = int(float(row["toc"]))
            except KeyError:
                eph.toc = int(float(row["GST_TOW"]))
            eph.week = int(float(row["WN"]))

            # Clock correction
            eph.af0 = float(row["af0"])
            eph.af1 = float(row["af1"])
            eph.af2 = float(row["af2"])

            # Orbital parameters
            eph.e = float(row["eccen"])
            eph.sqrta = float(row["sqrt_A"])
            eph.dn = float(row["delta_N"])
            eph.m0 = float(row["M0"])
            eph.omega = float(row["omega"])
            eph.OMEGA = float(row["OMEGA_0"])
            eph.OMEGA_DOT = float(row["OMEGA_DOT"])
            eph.i0 = float(row["i0"])
            eph.IDOT = float(row["IDOT"])

            # Correction terms
            eph.cuc = float(row["Cuc"])
            eph.cus = float(row["Cus"])
            eph.crc = float(row["Crc"])
            eph.crs = float(row["Crs"])
            eph.cic = float(row["Cic"])
            eph.cis = float(row["Cis"])

            # Additional info
            eph.prn = row["PRN"]
            try:
                eph.health = float(row["health"])
            except KeyError:
                eph.health = float(row["E1B_HS"])

            ephemerides.append(eph)

    return ephemerides


if __name__ == "__main__":
    # Read ephemerides from CSV
    gps_nav_data = read_nav_csv(
        csv_file="/home/amuls/cylab/TESTDATA/flepos/BERT/RX3/BERT00BEL_R_20243640700_41H_MN_GPS_LNAV.csv"
    )

    # Use first available ephemeris
    eph = gps_nav_data[0]

    # Calculate position at specific time

    for t in range(eph.toe, eph.toe + 3600, 300):
        x, y, z = eph.compute_satellite_position(t)

        print(
            f"GPS PRN: {eph.prn} at {t}: {x:15.3f}, {y:15.3f}, {z:15.3f} | {np.sqrt(x**2 + y**2 + z**2):15.3f}"
        )

    # Read ephemerides from CSV
    gal_nav_data = read_nav_csv(
        csv_file="/home/amuls/cylab/TESTDATA/flepos/BERT/RX3/BERT00BEL_R_20243640700_41H_MN_Galileo_INAV.csv"
    )

    # Use first available ephemeris
    eph = gal_nav_data[0]

    # Calculate position at specific time

    for t in range(eph.toe, eph.toe + 3600, 300):
        x, y, z = eph.compute_satellite_position(t)

        print(
            f"GAL PRN: {eph.prn} at {t}: {x:15.3f}, {y:15.3f}, {z:15.3f} | {np.sqrt(x**2 + y**2 + z**2):15.3f}"
        )
