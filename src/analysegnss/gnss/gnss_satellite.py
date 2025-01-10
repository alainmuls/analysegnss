import numpy as np


class Satellite:
    def __init__(self, orbital_params):
        # Orbital parameters
        self.A = orbital_params["semi_major_axis"]
        self.e = orbital_params["eccentricity"]
        self.i_0 = orbital_params["inclination"]
        self.OMEGA_0 = orbital_params["right_ascension"]
        self.omega = orbital_params["argument_perigee"]
        self.t_oe = orbital_params["reference_time"]

        # Correction terms
        self.C_us = orbital_params["C_us"]
        self.C_uc = orbital_params["C_uc"]
        self.C_rs = orbital_params["C_rs"]
        self.C_rc = orbital_params["C_rc"]
        self.C_is = orbital_params["C_is"]
        self.C_ic = orbital_params["C_ic"]

        # Motion parameters
        self.IDOT = orbital_params["IDOT"]
        self.OMEGA_dot = orbital_params["OMEGA_dot"]
        self.OMEGA_E = orbital_params["OMEGA_E"]  # Earth rotation rate

    def time_from_epoch(self, t):
        tk = t - self.t_oe
        if tk > 302400:
            tk -= 604800
        elif tk < -302400:
            tk += 604800

        return tk

    def eccentric_anomaly(self, t_k):
        # Implementation of Kepler's equation solver would go here
        # This is a simplified version
        M = self.M0 + t_k * (
            np.sqrt(self.GM / (self.A**3)) + self.delta_n
        )  # Mean anomaly
        E = M  # Initial guess
        for _ in range(10):
            E = M + self.e * np.sin(E)
        return E

    def get_position(self, t):
        # Time from ephemeris reference epoch
        t_k = self.time_from_epoch(t)

        # Eccentric Anomaly
        E_k = self.eccentric_anomaly(t_k)

        # True Anomaly
        v_k = np.arctan2(np.sqrt(1 - self.e**2) * np.sin(E_k), np.cos(E_k) - self.e)

        # Argument of Latitude
        AOL = v_k + self.omega

        # Second Harmonic Perturbations
        du_k = self.C_us * np.sin(2 * AOL) + self.C_uc * np.cos(2 * AOL)
        dr_k = self.C_rs * np.sin(2 * AOL) + self.C_rc * np.cos(2 * AOL)
        di_k = self.C_is * np.sin(2 * AOL) + self.C_ic * np.cos(2 * AOL)

        # Corrected values
        u_k = AOL + du_k
        r_k = self.A * (1 - self.e * np.cos(E_k)) + dr_k
        i_k = self.i_0 + di_k + self.IDOT * t_k

        # Positions in orbital plane
        x_kp = r_k * np.cos(u_k)
        y_kp = r_k * np.sin(u_k)

        # Corrected longitude of ascending node
        OMEGA_k = (
            self.OMEGA_0
            + (self.OMEGA_dot - self.OMEGA_E) * t_k
            - self.OMEGA_E * self.t_oe
        )

        # Earth-fixed coordinates (TO BE CHECKED)
        x = x_kp * np.cos(OMEGA_k) - y_kp * np.cos(i_k) * np.sin(OMEGA_k)
        y = x_kp * np.sin(OMEGA_k) + y_kp * np.cos(i_k) * np.cos(OMEGA_k)
        z = y_kp * np.sin(i_k)

        return x, y, z


orbital_params = {
    "semi_major_axis": 26559.5,  # km
    "eccentricity": 0.01,
    "inclination": 55.0 * np.pi / 180,  # convert degrees to radians
    "right_ascension": 0.0,
    "argument_perigee": 0.0,
    "reference_time": 0.0,
    "C_us": 0.0,
    "C_uc": 0.0,
    "C_rs": 0.0,
    "C_rc": 0.0,
    "C_is": 0.0,
    "C_ic": 0.0,
    "IDOT": 0.0,
    "OMEGA_dot": 0.0,
    "OMEGA_E": 7.2921151467e-5,  # rad/sec
}

satellite = Satellite(orbital_params)
x, y, z = satellite.get_position(3600)  # get position after 1 hour
print(f"Position: x={x:.2f}, y={y:.2f}, z={z:.2f} km")


def select_ephemeris(nav_messages, desired_time):
    best_message = None
    min_time_difference = float("inf")

    for message in nav_messages:
        time_difference = abs(message.toe - desired_time)

        # Typical validity period is ±2 hours from TOE
        if time_difference < min_time_difference and time_difference <= 7200:
            min_time_difference = time_difference
            best_message = message

    return best_message
