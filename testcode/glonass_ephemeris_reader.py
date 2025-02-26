import csv

import numpy as np

from src.analysegnss.gnss.glonass_ephemeris import GLONASSEphemeris


def read_glonass_nav_csv(csv_file):
    ephemerides = []

    with open(csv_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            eph = GLONASSEphemeris()

            # Time parameters
            eph.week = int(float(row["WKNR"]))
            eph.tow = float(row["TOW"])
            eph.tk = int(row["tk"])

            # Position and velocity
            eph.x = float(row["X"])
            eph.y = float(row["Y"])
            eph.z = float(row["Z"])
            eph.vx = float(row["VX"])
            eph.vy = float(row["VY"])
            eph.vz = float(row["VZ"])

            # Acceleration terms
            eph.ax = float(row["AX"])
            eph.ay = float(row["AY"])
            eph.az = float(row["AZ"])

            # Clock correction
            eph.tau_n = float(row["TauN"])
            eph.gamma_n = float(row["GammaN"])

            # Additional info
            eph.prn = int(row["PRN"])
            eph.freq_num = int(row["freqNum"])
            eph.health = int(row["health"])

            ephemerides.append(eph)

    return ephemerides


if __name__ == "__main__":
    glonass_csv = "/home/amuls/cylab/TESTDATA/flepos/BERT/RX3/BERT00BEL_R_20243640700_41H_MN_Glonass_FDMA.csv"

    print("\nProcessing GLONASS data")
    nav_data = read_glonass_nav_csv(csv_file=glonass_csv)

    # Use first available ephemeris
    eph = nav_data[0]

    # Calculate position at specific times
    base_time = eph.tk
    for t in range(0, 3600, 300):  # Calculate for one hour, every 5 minutes
        current_time = base_time + t
        x, y, z = eph.runge_kutta4(t=current_time)

        print(
            f"GLONASS PRN: {eph.prn} at {eph.week} {current_time}: "
            f"{x*1000:15.3f}, {y*1000:15.3f}, {z*1000:15.3f} | "
            f"{np.sqrt(x**2 + y**2 + z**2)*1000:15.3f}"
        )
