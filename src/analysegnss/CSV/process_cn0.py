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
