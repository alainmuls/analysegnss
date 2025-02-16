import numpy as np
from datetime import datetime, timedelta

from src.analysegnss.config import GM_GPS, OMGE_GPS, GM_GAL, OMGE_GAL, GM_BDS, OMGE_BDS


class GNSSEphemeris:
    def __init__(self):
        # Satellite identification
        self.gnss = None
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

    def calculate_GPS_GAL_coordinates(self, t: float) -> tuple:
        match self.gnss:
            case "G":
                GM = GM_GPS
                OMGE = OMGE_GPS
            case "E":
                GM = GM_GAL
                OMGE = OMGE_GAL
            case "C":
                GM = GM_BDS
                OMGE = OMGE_BDS
            case _:
                raise ValueError(f"Unknown GNSS: {self.gnss}")  # type: ignore

        # Semi-major axis
        A = self.sqrta * self.sqrta

        # Time from ephemeris reference epoch
        tk = t - self.toe

        # Mean motion
        n0 = np.sqrt(GM / (A * A * A))
        n = n0 + self.dn

        # Mean anomaly
        Mk = self.m0 + n * tk

        # Solve Kepler's equation iteratively
        Ek = Mk
        for _ in range(10):
            E_old = Ek
            Ek = Mk + self.e * np.sin(Ek)
            if abs(Ek - E_old) < 1e-12:
                break

        # Position calculation in orbital plane
        # True anomaly
        vk = np.arctan2(
            np.sqrt(1.0 - self.e * self.e) * np.sin(Ek), np.cos(Ek) - self.e
        )
        # Argument of latitude
        phik = vk + self.omega

        # Second harmonic corrections
        cos_2phik = np.cos(2.0 * phik)
        sin_2phik = np.sin(2.0 * phik)

        # Argument of latitude, Orbit radius and inclination correction
        duk = self.cus * sin_2phik + self.cuc * cos_2phik
        drk = self.crs * sin_2phik + self.crc * cos_2phik
        dik = self.cis * sin_2phik + self.cic * cos_2phik

        # Corrected radius, argument of latitude and inclination
        uk = phik + duk
        rk = A * (1.0 - self.e * np.cos(Ek)) + drk
        ik = self.i0 + dik + self.IDOT * tk

        # Positions in orbital plane
        xk_orbit = rk * np.cos(uk)
        yk_orbit = rk * np.sin(uk)


        # corrected longitude of ascending node (without accounting for Earth's rotation)
        OMEGA_k_eci = self.OMEGA + self.OMEGA_DOT * tk

        # Convert orbital plane to ECI
        X_ECI = xk_prime * np.cos(OMEGA_k_eci) - yk_prime * np.cos(ik) * np.sin(OMEGA_k_eci)
        Y_ECI = xk_prime * np.sin(OMEGA_k_eci) + yk_prime * np.cos(ik) * np.cos(OMEGA_k_eci)
        Z_ECI = yk_prime * np.sin(ik)


        # Rotation matrix around z axis 
        rot_angle = -OMGE * t # correct for earth's rotation  
        rot_z = np.array([[np.cos(rot_angle), -np.sin(rot_angle), 0],
                            [np.sin(rot_angle), np.cos(rot_angle), 0],
                            [0, 0, 1]])
        
        # rotate ECI to ECEF
        x, y, z = np.dot(rot_z, np.array([X_ECI, Y_ECI, Z_ECI]))
                # For BDS the coordinates are in the CGCS system, so convert to WGS84
        if self.gnss == "C":
            x, y, z = self.transform_cgcs_to_wgs84(x, y, z)
        
        return x, y, z    
        
        # """
        #         # Positions in orbital plane
        # xk_orbit = rk * np.cos(uk)
        # yk_orbit = rk * np.sin(uk)

        # # Corrected longitude of ascending node with Earth rotation
        # OMEGA_k = self.OMEGA + (self.OMEGA_DOT - OMGE) * tk - OMGE * self.toe

        # # Earth rotation correction matrix
        # cos_Omega = np.cos(OMEGA_k)
        # sin_Omega = np.sin(OMEGA_k)
        # cos_incl = np.cos(ik)
        # sin_incl = np.sin(ik)

        # # ECEF coordinates
        # x = xk_orbit * cos_Omega - yk_orbit * cos_incl * sin_Omega
        # y = xk_orbit * sin_Omega + yk_orbit * cos_incl * cos_Omega
        # z = yk_orbit * sin_incl

        # # For BDS the coordinates are in the CGCS system, so convert to WGS84
        # if self.gnss == "C":
        #     x, y, z = self.transform_cgcs_to_wgs84(x, y, z)
       
        # return x, y, z

    def is_valid(self, t: float) -> bool:
        """
        Check if ephemeris is valid for given time
        Args:
            t: GPS time in seconds of week
        Returns:
            bool: True if ephemeris is valid
        """
        time_difference = abs(t - self.toe)
        return time_difference <= 7200  # Valid for ±2 hours

    def transform_cgcs_to_wgs84(
        self, x: float, y: float, z: float
    ) -> tuple[float, float, float]:
        """Transform coordinates from BDS CGCS2000 to WGS84.

        Args:
            x, y, z: Coordinates in CGCS2000 frame (meters)
        Returns:
            tuple: (x, y, z) coordinates in WGS84 frame (meters)
        """
        # Translation parameters (meters)
        dx = -0.99
        dy = -1.90
        dz = -0.76

        # Scale parameter (ppb)
        scale = -0.000069 * 1e-9

        # Rotation parameters (radians)
        rx = -0.000034 * 4.8481e-6
        ry = 0.000002 * 4.8481e-6
        rz = 0.000023 * 4.8481e-6

        # Apply Helmert transformation
        x_wgs = (1 + scale) * (x + rz * y - ry * z) + dx
        y_wgs = (1 + scale) * (-rz * x + y + rx * z) + dy
        z_wgs = (1 + scale) * (ry * x - rx * y + z) + dz

        return (x_wgs, y_wgs, z_wgs)


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
