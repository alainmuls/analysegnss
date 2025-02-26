import numpy as np


class SP3Interpolator:
    def __init__(self, times, positions):
        self.degree = 16
        self.times = times
        self.positions = positions

    def lagrange_interpolation(self, t):
        """
        Interpolate satellite position using Lagrange polynomial
        Args:
            t: time for interpolation
        Returns:
            x, y, z: interpolated coordinates
        """
        x = y = z = 0.0

        for i in range(self.degree + 1):
            # Calculate Lagrange basis polynomial
            li = 1.0
            for j in range(self.degree + 1):
                if i != j:
                    li *= (t - self.times[j]) / (self.times[i] - self.times[j])

            # Add contribution to interpolated position
            x += self.positions[i][0] * li
            y += self.positions[i][1] * li
            z += self.positions[i][2] * li

        return x, y, z

    def get_position(self, t):
        """
        Get interpolated position at time t
        Ensures we use the correct window of points around t
        """
        # Find the appropriate window of points
        idx = np.searchsorted(self.times, t)
        start_idx = max(0, idx - self.degree // 2)
        end_idx = min(len(self.times), start_idx + self.degree + 1)
        start_idx = end_idx - self.degree - 1

        # Create interpolator with window
        window_times = self.times[start_idx:end_idx]
        window_positions = self.positions[start_idx:end_idx]

        return self.lagrange_interpolation(t)


# Sample data from SP3 file
times = np.array([0, 900, 1800, 2700, 3600])  # seconds
positions = np.array(
    [
        [x1, y1, z1],
        [x2, y2, z2],
        # ... more positions ...
    ]
)

interpolator = SP3Interpolator(times, positions)
x, y, z = interpolator.get_position(1350)  # interpolate at 1350 seconds
