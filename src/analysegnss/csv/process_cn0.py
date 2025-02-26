def analyze_cn0_values(csv_path: str, gnss: str, signal: str) -> pl.DataFrame:
    # Read the CSV file
    df = pl.read_csv(csv_path)

    # Filter for specific GNSS and signal type
    filtered_df = df.filter((pl.col("GNSS") == gnss) & (pl.col("sigt") == signal))

    # Round TOW to nearest 10 seconds (10000 milliseconds)
    filtered_df = filtered_df.with_columns(
        pl.col("TOW").map_elements(lambda x: (x // 10000) * 10000).alias("epoch")
    )

    # Group by epoch and calculate statistics
    result_df = filtered_df.group_by("epoch").agg(
        [
            pl.col("S").mean().alias("mean_cn0"),
            pl.col("PRN").count().alias("num_sats"),
            pl.col("PRN").list().alias("tracked_prns"),
        ]
    )

    return result_df.sort("epoch")


def process_multiple_days(csv_files: list, gnss: str, signal: str, output_file: str):
    # Process each file
    results = []
    for csv_file in csv_files:
        daily_results = analyze_cn0_values(csv_file, gnss, signal)
        results.append(daily_results)

    # Combine all results
    combined_df = pl.concat(results)

    # Sort by epoch and save to file
    combined_df.sort("epoch").write_csv(output_file)


csv_files = ["day1.csv", "day2.csv", "day3.csv"]  # Your 3 months of daily files
process_multiple_days(csv_files, "G", "1C", "cn0_analysis_results.csv")


SP3_File


from analysegnss.SP3.SP3_class import SP3_File
import numpy as np


def calculate_elevation_angles(self, sp3_file, station_xyz):
    """
    Calculate elevation angles for all epochs using SP3 precise orbits

    Args:
        sp3_file: Path to SP3 file
        station_xyz: Station coordinates (X,Y,Z) in ECEF
    """
    # Initialize SP3 reader
    sp3 = SP3_File(sp3_file)

    # Convert station ECEF to numpy array
    station = np.array(station_xyz)

    def ecef_to_enu(sat_pos, station_pos):
        # Calculate satellite-station vector
        vector = sat_pos - station_pos

        # Convert from ECEF to ENU
        # First compute rotation matrix for station location
        lon = np.arctan2(station_pos[1], station_pos[0])
        lat = np.arctan2(
            station_pos[2], np.sqrt(station_pos[0] ** 2 + station_pos[1] ** 2)
        )

        # Rotation matrix
        sin_lon, cos_lon = np.sin(lon), np.cos(lon)
        sin_lat, cos_lat = np.sin(lat), np.cos(lat)

        R = np.array(
            [
                [-sin_lon, cos_lon, 0],
                [-sin_lat * cos_lon, -sin_lat * sin_lon, cos_lat],
                [cos_lat * cos_lon, cos_lat * sin_lon, sin_lat],
            ]
        )

        # Transform to ENU
        enu = R @ vector

        # Calculate elevation angle
        e, n, u = enu
        elevation = np.arctan2(u, np.sqrt(e**2 + n**2))
        return np.degrees(elevation)

    # Calculate elevation for each epoch/PRN combination
    elevations = []
    for _, row in self.df_cn0.iter_rows():
        sat_pos = sp3.get_interpolated_position(
            gnss=self.GNSS, prn=row["PRN"], wknr=row["WKNR"], tow=row["TOW"]
        )
        if sat_pos is not None:
            elev = ecef_to_enu(np.array(sat_pos), station)
            elevations.append(elev)
        else:
            elevations.append(None)

    # Add elevations to dataframe
    self.df_cn0 = self.df_cn0.with_columns(pl.Series("elevation", elevations))


station_pos = [X, Y, Z]  # Your station ECEF coordinates
gnss_data.calculate_elevation_angles("precise_orbits.sp3", station_pos)





https://github.com/arthurdjn/gnsstools

https://github.com/neuromorphicsystems/sp3?tab=readme-ov-file#sp3

https://gnss-lib-py.readthedocs.io/en/latest/tutorials/parsers/tutorials_sp3_notebook.html

https://github.com/GNSSpy-Project/gnsspy