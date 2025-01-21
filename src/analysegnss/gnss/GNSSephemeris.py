import numpy as np
from datetime import datetime, timedelta

from src.analysegnss.config import GM, OMEGA_EARTH, SECS_IN_WEEK


class GNSSEphemeris:
    def __init__(self):
        # Satellite identification
        self.prn = None
        self.health = None

        # Time parameters
        self.toe = None  # Time of Ephemeris
        self.toc = None  # Time of Clock
        self.week = None

        # Clock correction parameters
        self.af0 = None  # Clock bias (seconds)
        self.af1 = None  # Clock drift (sec/sec)
        self.af2 = None  # Clock drift rate (sec/sec^2)

        # Orbital parameters
        self.e = None  # Eccentricity
        self.sqrta = None  # Square root of semi-major axis
        self.dn = None  # Mean motion correction
        self.m0 = None  # Mean anomaly at reference time
        self.omega = None  # Argument of perigee
        self.OMEGA = None  # Right ascension of ascending node
        self.OMEGA_DOT = None  # Rate of right ascension
        self.i0 = None  # Inclination angle at reference time
        self.IDOT = None  # Rate of inclination angle

        # Correction terms
        self.cuc = None  # Cosine latitude
        self.cus = None  # Sine latitude
        self.crc = None  # Cosine radius
        self.crs = None  # Sine radius
        self.cic = None  # Cosine inclination
        self.cis = None  # Sine inclination

        self.IODE = None  # Issue of Data

    # def compute_satellite_position(self, t: float) -> tuple:
    #     """
    #     Compute satellite position at time t
    #     Args:
    #         t: GPS time in seconds of week
    #     Returns:
    #         x, y, z: ECEF coordinates in meters
    #     """
    #     # Semi-major axis
    #     A = self.sqrta * self.sqrta

    #     # Time from ephemeris reference epoch
    #     tk = t - self.toe
    #     if tk > SECS_IN_WEEK / 2:
    #         tk -= SECS_IN_WEEK
    #     elif tk < -SECS_IN_WEEK / 2:
    #         tk += SECS_IN_WEEK

    #     # Mean motion
    #     n0 = np.sqrt(GM / (A * A * A))
    #     n = n0 + self.dn

    #     # Mean anomaly
    #     Mk = self.m0 + n * tk

    #     # Solve Kepler's equation for eccentric anomaly
    #     Ek = Mk
    #     for _ in range(10):
    #         Ek = Mk + self.e * np.sin(Ek)

    #     # True anomaly
    #     vk = np.arctan2(
    #         np.sqrt(1.0 - self.e * self.e) * np.sin(Ek), np.cos(Ek) - self.e
    #     )

    #     # Argument of latitude
    #     phik = vk + self.omega

    #     # Second harmonic corrections
    #     duk = self.cus * np.sin(2.0 * phik) + self.cuc * np.cos(2.0 * phik)
    #     drk = self.crs * np.sin(2.0 * phik) + self.crc * np.cos(2.0 * phik)
    #     dik = self.cis * np.sin(2.0 * phik) + self.cic * np.cos(2.0 * phik)

    #     # Corrected argument of latitude, radius, and inclination
    #     uk = phik + duk
    #     rk = A * (1.0 - self.e * np.cos(Ek)) + drk
    #     ik = self.i0 + dik + self.IDOT * tk

    #     # Position in orbital plane
    #     xk_prime = rk * np.cos(uk)
    #     yk_prime = rk * np.sin(uk)

    #     # Corrected longitude of ascending node
    #     OMEGA_k = self.OMEGA + (self.OMEGA_DOT - OMEGA_EARTH) * tk - OMEGA_EARTH * t

    #     # Earth-fixed coordinates
    #     x = xk_prime * np.cos(OMEGA_k) - yk_prime * np.cos(ik) * np.sin(OMEGA_k)
    #     y = xk_prime * np.sin(OMEGA_k) + yk_prime * np.cos(ik) * np.cos(OMEGA_k)
    #     z = yk_prime * np.sin(ik)

    #     return x, y, z

    def compute_satellite_position(self, t: float) -> tuple:
        # Semi-major axis
        A = self.sqrta * self.sqrta

        # Time from ephemeris reference epoch
        tk = t - self.toe

        # Mean motion
        n0 = np.sqrt(GM / (A * A * A))
        n = n0 + self.dn

        # Mean anomaly
        Mk = self.m0 + n * tk

        # Eccentric anomaly
        Ek = Mk
        for _ in range(10):
            Ek = Mk + self.e * np.sin(Ek)

        # Position calculation in orbital plane
        vk = np.arctan2(
            np.sqrt(1.0 - self.e * self.e) * np.sin(Ek), np.cos(Ek) - self.e
        )
        phik = vk + self.omega

        # Second harmonic corrections
        duk = self.cus * np.sin(2.0 * phik) + self.cuc * np.cos(2.0 * phik)
        drk = self.crs * np.sin(2.0 * phik) + self.crc * np.cos(2.0 * phik)
        dik = self.cis * np.sin(2.0 * phik) + self.cic * np.cos(2.0 * phik)

        # Corrected radius, argument of latitude and inclination
        uk = phik + duk
        rk = A * (1.0 - self.e * np.cos(Ek)) + drk
        ik = self.i0 + dik + self.IDOT * tk

        # Positions in orbital plane
        xk_prime = rk * np.cos(uk)
        yk_prime = rk * np.sin(uk)

        # corrected longitude of ascending node (without accounting for Earth's rotation)
        OMEGA_k_eci = self.OMEGA + self.OMEGA_DOT * tk

        # Convert orbital plane to ECI
        X_ECI = xk_prime * np.cos(OMEGA_k_eci) - yk_prime * np.cos(ik) * np.sin(OMEGA_k_eci)
        Y_ECI = xk_prime * np.sin(OMEGA_k_eci) + yk_prime * np.cos(ik) * np.cos(OMEGA_k_eci)
        Z_ECI = yk_prime * np.sin(ik)


        # Rotation matrix around z axis (counterclockwise)
        rot_angle = -OMEGA_EARTH * t # angle of rotation (needs to be negative to compensate for earth's rotation)
        rot_z = np.array([[np.cos(rot_angle), -np.sin(rot_angle), 0],
                            [np.sin(rot_angle), np.cos(rot_angle), 0],
                            [0, 0, 1]])
        
        # rotate ECI to ECEF
        X_ECEF, Y_ECEF, Z_ECEF = np.dot(rot_z, np.array([X_ECI, Y_ECI, Z_ECI]))
        
        
        """
        # direct conversion from orbital plane to ECEF
        
        # Corrected longitude of ascending node with Earth rotation
        OMEGA_k = self.OMEGA + (self.OMEGA_DOT - OMEGA_EARTH) * tk - OMEGA_EARTH * t

        # Earth rotation correction matrix
        cos_O = np.cos(OMEGA_k)
        sin_O = np.sin(OMEGA_k)
        cos_i = np.cos(ik)
        sin_i = np.sin(ik)

        
        # Final ECEF coordinates
        x = xk_prime * cos_O - yk_prime * cos_i * sin_O
        y = xk_prime * sin_O + yk_prime * cos_i * cos_O
        z = yk_prime * sin_i
        """
       
        return X_ECEF, Y_ECEF, Z_ECEF

    def is_valid(self, t):
        """
        Check if ephemeris is valid for given time
        Args:
            t: GPS time in seconds of week
        Returns:
            bool: True if ephemeris is valid
        """
        time_difference = abs(t - self.toe)
        return time_difference <= 7200  # Valid for ±2 hours

    # Create and populate ephemeris object


# eph = GNSSEphemeris()
# eph.prn = 1
# eph.toe = 345600  # Time of ephemeris in seconds of GPS week
# eph.sqrta = 5153.79589081
# eph.e = 0.00223578442819
# # ... set other parameters ...

# # Calculate position at specific time
# gps_time = 346800  # GPS seconds of week
# if eph.is_valid(gps_time):
#     x, y, z = eph.compute_satellite_position(gps_time)
#     print(f"Satellite position (ECEF): {x:.2f}, {y:.2f}, {z:.2f} meters")
