import csv

from rich import print

from .GNSSephemeris import GNSSEphemeris


class GNSSNavReader:
    """GNSSNavReader reads GNSS navigation data from a CSV file for GPS, GAL & BDS."""

    def __init__(self, csv_file: str):
        self.csv_file = csv_file
        self.ephemerides = []

    def read_GEC_nav_csv(self):
        with open(self.csv_file, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:

                eph = GNSSEphemeris()

                # Time parameters
                eph.toe = int(float(row["toe"]))
                try:
                    eph.toc = int(float(row["toc"]))
                except KeyError:
                    eph.toc = int(float(row["GST_TOW"]))
                try:
                    eph.week = int(float(row["WN"]))
                except KeyError:
                    eph.week = int(float(row["BDS_WN"]))

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
                eph.prn = int(row["PRN"])
                try:
                    eph.health = float(row["health"])
                except KeyError:
                    try:
                        eph.health = float(row["E1B_HS"])
                    except KeyError:
                        eph.health = float(row["SatH1"])

                try:
                    eph.IODE = int(float(row["IODE"]))
                except KeyError:
                    eph.IODE = None

                self.ephemerides.append(eph)

    def get_ephemeris(self, t: float) -> GNSSEphemeris:
        """get the ephemeris record which has toe closest to the given time

        Args:
            t (float): time in seconds of week  [0, 604800]

        Returns:
            GNSSEphemeris: GEC ephemeris record
        """
        if not self.ephemerides:
            return None

        # Find ephemeris with minimum time difference to t
        closest_eph = min(self.ephemerides, key=lambda x: abs(x.toe - t))
        return closest_eph

    def get_all_ephemeris(self) -> list[GNSSEphemeris]:
        """returns all ephemeris read from CSV file

        Returns:
            list: list of ephemeris records
        """
        return self.ephemerides
