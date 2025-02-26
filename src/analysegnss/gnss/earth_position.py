import numpy as np


class EarthPosition:
    def __init__(self, lat=0.0, lon=0.0, alt=0.0):
        # WGS84 ellipsoid constants
        self.a = 6378137.0  # semi-major axis in meters
        self.f = 1 / 298.257223563  # flattening
        self.b = self.a * (1 - self.f)  # semi-minor axis
        self.e2 = 2 * self.f - self.f * self.f  # eccentricity squared

        # Position
        self.lat = np.radians(lat)  # latitude in radians
        self.lon = np.radians(lon)  # longitude in radians
        self.alt = alt  # altitude in meters

    def to_ecef(self):
        """Convert geodetic coordinates to ECEF"""
        N = self.a / np.sqrt(1 - self.e2 * np.sin(self.lat) ** 2)

        x = (N + self.alt) * np.cos(self.lat) * np.cos(self.lon)
        y = (N + self.alt) * np.cos(self.lat) * np.sin(self.lon)
        z = (N * (1 - self.e2) + self.alt) * np.sin(self.lat)

        return x, y, z

    def from_ecef(self, x, y, z):
        """Convert ECEF coordinates to geodetic"""
        p = np.sqrt(x * x + y * y)
        theta = np.arctan2(z * self.a, p * self.b)

        self.lon = np.arctan2(y, x)
        self.lat = np.arctan2(
            z + self.e2 * self.b * np.sin(theta) ** 3,
            p - self.e2 * self.a * np.cos(theta) ** 3,
        )

        N = self.a / np.sqrt(1 - self.e2 * np.sin(self.lat) ** 2)
        self.alt = p / np.cos(self.lat) - N

        return self.lat, self.lon, self.alt

    def to_enu(self, x, y, z):
        """Convert ECEF to local East-North-Up coordinates"""
        x_ref, y_ref, z_ref = self.to_ecef()

        dx = x - x_ref
        dy = y - y_ref
        dz = z - z_ref

        # Rotation matrix
        sin_lat = np.sin(self.lat)
        cos_lat = np.cos(self.lat)
        sin_lon = np.sin(self.lon)
        cos_lon = np.cos(self.lon)

        east = -sin_lon * dx + cos_lon * dy
        north = -sin_lat * cos_lon * dx - sin_lat * sin_lon * dy + cos_lat * dz
        up = cos_lat * cos_lon * dx + cos_lat * sin_lon * dy + sin_lat * dz

        return east, north, up

    def calculate_elevation_azimuth(self, x, y, z):
        """
        Calculate elevation and azimuth angles to satellite
        Args:
            x, y, z: ECEF coordinates of satellite
        Returns:
            elevation: Elevation angle in degrees
            azimuth: Azimuth angle in degrees
        """
        # Convert satellite ECEF to ENU
        e, n, u = self.to_enu(x, y, z)

        # Calculate horizontal distance
        horizontal = np.sqrt(e * e + n * n)

        # Calculate elevation and azimuth
        elevation = np.degrees(np.arctan2(u, horizontal))
        azimuth = np.degrees(np.arctan2(e, n)) % 360

        return elevation, azimuth


# Create position for a location
position = EarthPosition(lat=40.7128, lon=-74.0060, alt=100)  # New York City

# Get ECEF coordinates
x, y, z = position.to_ecef()
print(f"ECEF coordinates: {x:.2f}, {y:.2f}, {z:.2f}")

# Convert satellite position to local ENU
sat_x, sat_y, sat_z = some_satellite_position()  # from GPS/GLONASS calculation
e, n, u = position.to_enu(sat_x, sat_y, sat_z)
print(f"Local ENU coordinates: {e:.2f}, {n:.2f}, {u:.2f}")

el, az = position.calculate_elevation_azimuth(sat_x, sat_y, sat_z)
print(f"Satellite elevation: {el:.2f}°, azimuth: {az:.2f}°")
