import numpy as np


class GLONASSEphemeris:
    def __init__(self):
        # Previous initialization code...

        # Constants
        self.GM = 398600.4418  # Earth's gravitational constant km³/s²
        self.AE = 6378.136  # Earth's radius km
        self.J2 = 1082.63e-6  # Second zonal harmonic
        self.OMEGA_E = 7.292115e-5  # Earth's rotation rate rad/s

        # Time parameters
        self.week = None
        self.tow = None
        self.tk = None

        # Position and velocity and acceleration
        self.x = None
        self.y = None
        self.z = None
        self.vx = None
        self.vy = None
        self.vz = None
        self.ax = None
        self.ay = None
        self.az = None

        # Clock correction
        self.tau_n = None
        self.gamma_n = None

        # Additional info
        self.prn = None
        self.freq_num = None
        self.health = None

    def compute_acceleration(self, pos):
        x, y, z = pos
        r = np.sqrt(x * x + y * y + z * z)

        # Gravitational acceleration
        factor = -self.GM / (r * r * r)
        ax = factor * x
        ay = factor * y
        az = factor * z

        # J2 perturbation
        factor_j2 = 1.5 * self.J2 * self.GM * self.AE * self.AE / (r * r * r * r * r)

        ax += factor_j2 * x * (5 * z * z / (r * r) - 1)
        ay += factor_j2 * y * (5 * z * z / (r * r) - 1)
        az += factor_j2 * z * (5 * z * z / (r * r) - 3)

        return np.array([ax, ay, az])

    def runge_kutta4(self, t):
        dt = 1.0  # Integration step (1 second)
        steps = int(abs(t - self.tk))

        pos = np.array([self.x, self.y, self.z])
        vel = np.array([self.vx, self.vy, self.vz])

        for _ in range(steps):
            # RK4 for position and velocity
            k1_pos = vel
            k1_vel = self.compute_acceleration(pos)

            k2_pos = vel + 0.5 * dt * k1_vel
            k2_vel = self.compute_acceleration(pos + 0.5 * dt * k1_pos)

            k3_pos = vel + 0.5 * dt * k2_vel
            k3_vel = self.compute_acceleration(pos + 0.5 * dt * k2_pos)

            k4_pos = vel + dt * k3_vel
            k4_vel = self.compute_acceleration(pos + dt * k3_pos)

            pos += (dt / 6.0) * (k1_pos + 2 * k2_pos + 2 * k3_pos + k4_pos)
            vel += (dt / 6.0) * (k1_vel + 2 * k2_vel + 2 * k3_vel + k4_vel)

        return pos
