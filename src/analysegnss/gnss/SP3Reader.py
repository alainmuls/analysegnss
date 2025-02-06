from datetime import datetime, timedelta
import numpy as np


class SP3Reader:
    def __init__(self, sp3_file):
        self.epochs = {}  # Dictionary to store positions by PRN and epoch
        self.read_sp3(sp3_file)

    def read_sp3(self, sp3_file):
        with open(sp3_file) as f:
            for line in f:
                if line[0] == "*":  # Epoch line
                    # Parse epoch time
                    year = int(line[3:7])
                    month = int(line[8:10])
                    day = int(line[11:13])
                    hour = int(line[14:16])
                    minute = int(line[17:19])
                    second = float(line[20:31])
                    epoch = datetime(year, month, day, hour, minute, int(second))

                elif line[0] == "P":  # Position line
                    # Parse satellite position
                    prn = line[1:4].strip()
                    x = float(line[4:18]) * 1000  # Convert to meters
                    y = float(line[18:32]) * 1000
                    z = float(line[32:46]) * 1000

                    # Store in dictionary
                    if prn not in self.epochs:
                        self.epochs[prn] = {"times": [], "positions": []}

                    self.epochs[prn]["times"].append(epoch)
                    self.epochs[prn]["positions"].append([x, y, z])

    def get_interpolation_window(self, prn, target_time, window_size=17):
        """
        Get positions window centered on target time
        Args:
            prn: Satellite PRN
            target_time: datetime object for desired interpolation time
            window_size: number of points for interpolation (default 17 for degree 16)
        """
        times = np.array(self.epochs[prn]["times"])
        positions = np.array(self.epochs[prn]["positions"])

        # Find closest epoch
        time_diffs = [(t - target_time).total_seconds() for t in times]
        center_idx = np.argmin(np.abs(time_diffs))

        # Get window indices
        half_window = window_size // 2
        start_idx = max(0, center_idx - half_window)
        end_idx = min(len(times), start_idx + window_size)
        start_idx = end_idx - window_size

        window_times = np.array(
            [(t - times[start_idx]).total_seconds() for t in times[start_idx:end_idx]]
        )
        window_positions = positions[start_idx:end_idx]

        return window_times, window_positions


# Read SP3 file and set up interpolator
reader = SP3Reader("precise_orbits.sp3")

# Get interpolation window for specific satellite and time
target_time = datetime(2023, 1, 1, 12, 0, 0)
prn = "G01"  # GPS satellite PRN
times, positions = reader.get_interpolation_window(prn, target_time)

# Create interpolator with window data
interpolator = SP3Interpolator(times, positions)

# Get interpolated position
target_seconds = 0  # Time relative to window start
x, y, z = interpolator.get_position(target_seconds)
