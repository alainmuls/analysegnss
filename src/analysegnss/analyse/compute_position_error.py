import argparse
import numpy as np
import logging
from typing import Tuple, Dict
import os
import sys

# third-party imports
from rich import print as rprint

# local imports
import analysegnss.gnss.crs_transformer as crs_transformer
from analysegnss.pnt.pnt_data_collector import pnt_data_collector
from analysegnss.utils import init_logger
from analysegnss.utils.argument_parser import (
    argument_parser_compute_position_error,
)

# computing the position error using the true position or the mean position
# When using the true position, we compute the Root Mean Square Error (RMSE) and the 95th percentile of the position error
# When using the mean position, we compute the standard error deviation and the 95th percentile of the position error
# RMSE and standard error deviation slightly differ in how they compute the error.
# RMSE does not apply the Bessel's correction (N-1 instead of N) compared to standard error deviation.
# RMSE is therefore used relative to the true position, while standard error deviation is used relative to the mean position.


def compute_position_error(
    parsed_args: argparse.Namespace,
    logger: logging.Logger,
) -> dict:
    """
    Compute the position error using the true position or the mean position.

    Args:
        parsed_args: argparse.Namespace
            - pos_ifn: list of pos files input filenames (str)
            - glab_ifn: list of gLABng files input filenames (str)
            - nmea_ifn: list of nmea files input filenames (str)
            - csv_ifn: list of csv files input filenames (str)
            - sd: boolean to add standard deviations to the dataframe

            CSV options:
            --columns_csv: list of columns to be read from CSV files (str)
            --sep: separator for CSV files (default: ',')
            --comment_prefix: comment prefix for CSV files (default: '#')
            --no_header: boolean to disable processing of header for CSV files (default: False)
            --skip_rows_after_header: number of rows to skip after the header for CSV files (default: 0)

        logger: logging.Logger
            logger object

    Returns:
        Tuple[float, float, float, float, float, float, float]: RMSE, standard error deviation, 95% confidence interval of the position error
    """

    # get the UTM and orthometric height data from the source
    easting, northing, orthoH = get_pnt_data_from_source(
        parsed_args=parsed_args, logger=logger
    )
    logger.debug(
        f"Extracted utm coordinates and orthometric height: {easting}, {northing}, {orthoH}"
    )

    # create 3D numpy arrays of the measured positions
    measured_positions_in_utm = np.column_stack(
        [
            np.concatenate(easting),
            np.concatenate(northing),
            np.concatenate(orthoH),
        ]
    )

    # Compute the position error
    if parsed_args.true_pos is not None:  # True position provided

        if parsed_args.ecef:  # True position provided in ECEF coordinates
            logger.info("True position provided in ECEF coordinates")
            x_true, y_true, z_true = parsed_args.true_pos
            logger.debug(f"Extracted true x, y, z: {x_true}, {y_true}, {z_true}")

            # convert x, y, z to easting, northing, orthometric_height
            true_easting, true_northing, true_ellh, true_orthoH, _, _ = (
                crs_transformer.ecef_to_utm_and_orthoH(x_true, y_true, z_true)
            )
            logger.debug(
                f"Converted true x, y, z to easting, northing, ellipsoidal height, orthometric height:\
                    {true_easting}, {true_northing}, {true_ellh}, {true_orthoH}"
            )

            # convert true position to numpy array
            true_positions_in_utm = np.column_stack(
                [true_easting, true_northing, true_orthoH]
            )

            # compute the position error
            computed_position_errors = compute_position_error_in_utm(
                logger=logger,
                measured_positions_in_utm=measured_positions_in_utm,
                true_positions_in_utm=true_positions_in_utm,
            )

        elif parsed_args.llh:
            logger.info("True position provided in LLH coordinates")
            lat_true, lon_true, ellh_true = parsed_args.true_pos
            logger.debug(
                f"Extracted true lat, lon, height: {lat_true}, {lon_true}, {ellh_true}"
            )
            # convert lat, lon, height to easting, northing, orthometric_height
            true_easting, true_northing, true_ellh, true_orthoH, _, _ = (
                crs_transformer.llh_to_utm_and_orthoH(lat_true, lon_true, ellh_true)
            )
            logger.debug(
                f"Converted true lat, lon, height to easting, northing, ellipsoidal height, orthometric height:\
                    {true_easting}, {true_northing}, {true_ellh}, {true_orthoH}"
            )

            # convert true position to numpy array
            true_positions_in_utm = np.column_stack(
                [true_easting, true_northing, true_orthoH]
            )

            # compute the position error
            computed_position_errors = compute_position_error_in_utm(
                logger=logger,
                measured_positions_in_utm=measured_positions_in_utm,
                true_positions_in_utm=true_positions_in_utm,
            )

        else:
            logger.info("True position provided in UTM coordinates")
            easting_true, northing_true, orthoH_true = parsed_args.true_pos
            logger.debug(
                f"Extracted true easting, northing, orthometric_height: {easting_true}, {northing_true}, {orthoH_true}"
            )

            # convert true position to numpy array
            true_positions_in_utm = np.array([easting_true, northing_true, orthoH_true])

            # compute the position error
            computed_position_errors = compute_position_error_in_utm(
                logger=logger,
                measured_positions_in_utm=measured_positions_in_utm,
                true_positions_in_utm=true_positions_in_utm,
            )

    else:
        logger.info("No true position provided, using mean position")

        # compute the mean position
        computed_position_errors = compute_position_error_in_utm(
            logger=logger,
            measured_positions_in_utm=measured_positions_in_utm,
        )

    # print the results
    logger.info(
        f"Standard error deviation (m): {computed_position_errors['stde_in_utm']}"
    )
    logger.info(f"95% percentile (m): {computed_position_errors['p95e_in_utm']}")
    logger.info(
        f"Euclidean distance error (m): {computed_position_errors['p95_distance_error']}"
    )
    logger.info(f"Reference position: {computed_position_errors['reference_position']}")

    rprint(f"\nStandard error deviation (m): {computed_position_errors['stde_in_utm']}")
    rprint(f"\n95% percentile (m): {computed_position_errors['p95e_in_utm']}")
    rprint(
        f"\nEuclidean distance error (m): {computed_position_errors['p95_distance_error']}\n"
    )
    rprint(f"Reference position: {computed_position_errors['reference_position']}")

    return computed_position_errors


def get_pnt_data_from_source(
    parsed_args: argparse.Namespace,
    logger: logging.Logger,
) -> Tuple[list[float], list[float], list[float]]:
    """Get PNT data from source using pnt_data_collector.py

    Args:
        parsed_args: argparse.Namespace (see compute_position_error())
        logger: logging.Logger

    Returns:
        Tuple[easting: list[float], northing: list[float], orthoH: list[float]]
    """

    # get the PNT data from the source
    standard_pnt_dfs, _ = pnt_data_collector(parsed_args=parsed_args, logger=logger)
    logger.debug(f"Extracted standard PNT dataframes: {standard_pnt_dfs}")

    logger.debug("Extracting UTM.E, UTM.N, orthoH coordinates from the PNT dataframe")

    # get the x, y, z coordinates from the PNT dataframes
    easting = []
    northing = []
    orthoH = []
    for pnt_df in standard_pnt_dfs.values():
        easting.append(pnt_df["UTM.E"])
        northing.append(pnt_df["UTM.N"])
        orthoH.append(pnt_df["orthoH"])

    logger.debug(f"Extracted utm coordinates: {easting}, {northing}, {orthoH}")

    return easting, northing, orthoH


def compute_position_error_in_utm(
    logger: logging.Logger,
    measured_positions_in_utm: np.ndarray,
    true_positions_in_utm: np.ndarray | None = None,
) -> dict:
    """
    Compute the Root Mean Square Error (RMSE), and 95% confidence interval of the position error using the true position.

    Args:
        measured_positions_in_utm (np.ndarray): measured positions in UTM coordinates
        true_positions_in_utm (np.ndarray): true positions in UTM coordinates

    Returns:
        dict: standard error deviation, 95 percentile of the position error, 95 percentile of the euclidean distance error, reference position
    """

    # Initialize reference position variables
    reference_position: np.ndarray
    reference_position_str: str

    if true_positions_in_utm is None:
        # mean of the measured positions
        reference_position = np.mean(measured_positions_in_utm, axis=0)
        reference_position_str = f"mean position: {reference_position}"
        logger.debug(f"Computed mean of the measured positions: {reference_position}")
        # compute the error between the measured and mean positions
        errors = measured_positions_in_utm - reference_position
        e_east, e_north, e_Height = errors[:, 0], errors[:, 1], errors[:, 2]
        logger.debug(
            f"Computed difference between measured and mean positions: {e_east}, {e_north}, {e_Height}"
        )

        # WARNING: Numpy std() seems to compute the mean of the errors as the new reference position...
        # This can be interesting if their is a fixed absolute offset/baseline between the measurements and the reference position.
        # Compute the standard error deviation using std() numpy function with N-1 degrees of freedom (ddof=1)
        # stde_east, stde_north, stde_Height = (
        #    np.std(e_east, ddof=1).item(),
        #    np.std(e_north, ddof=1).item(),
        #    np.std(e_Height, ddof=1).item(),
        # )

        # Compute the standard error deviation using the sum of the squared errors and Bessel correction
        stde_east = np.sqrt(np.sum(e_east**2) / (len(e_east) - 1)).item()
        stde_north = np.sqrt(np.sum(e_north**2) / (len(e_north) - 1)).item()
        stde_Height = np.sqrt(np.sum(e_Height**2) / (len(e_Height) - 1)).item()

        logger.debug(
            f"Computed standard error deviations (relative to mean position) : {stde_east}, {stde_north}, {stde_Height}"
        )

    else:
        # Compute the error between the measured and true positions
        reference_position = true_positions_in_utm
        reference_position_str = f"true position: {reference_position}"
        logger.debug(f"Computed true position: {reference_position}")

        # Compute the error between the measured and true positions
        errors = measured_positions_in_utm - reference_position
        e_east, e_north, e_Height = errors[:, 0], errors[:, 1], errors[:, 2]
        logger.debug(
            f"Computed difference between measured and true positions: {e_east}, {e_north}, {e_Height}"
        )

        # WARNING: Numpy std() seems to compute the mean of the errors as the new reference position...
        # This can be interesting if their is a fixed absolute offset/baseline between the measurements and the reference position.
        # Compute the standard error deviation using std() numpy function with N-1 degrees of freedom (ddof=1)
        # stde_east, stde_north, stde_Height = (
        #    np.std(e_east, ddof=1).item(),
        #    np.std(e_north, ddof=1).item(),
        #    np.std(e_Height, ddof=1).item(),
        # )

        # Compute the standard error deviation using the sum of the squared errors without the Bessel correction
        stde_east = np.sqrt(np.sum(e_east**2) / len(e_east)).item()
        stde_north = np.sqrt(np.sum(e_north**2) / len(e_north)).item()
        stde_Height = np.sqrt(np.sum(e_Height**2) / len(e_Height)).item()

        logger.debug(
            f"Computed standard error deviations (relative to true position) : {stde_east}, {stde_north}, {stde_Height}"
        )

    # Compute the 95% percentile of the error for each dimension
    p95_east, p95_north, p95_Height = (
        np.percentile(e_east, 95).item(),
        np.percentile(e_north, 95).item(),
        np.percentile(e_Height, 95).item(),
    )
    # euclidean distance error (95% percentile) between true and measured position
    euclidean_errors = np.sqrt(e_east**2 + e_north**2 + e_Height**2)
    p95_distance_error = np.percentile(euclidean_errors, 95).item()

    # store results in a dictionary
    computed_position_errors = {
        "stde_in_utm": tuple([stde_east, stde_north, stde_Height]),
        "p95e_in_utm": tuple([p95_east, p95_north, p95_Height]),
        "p95_distance_error": p95_distance_error,
        "reference_position": reference_position_str,
    }

    return computed_position_errors


def main():
    # get the script name for passing to argument_parser
    script_name = os.path.basename(__file__)

    # parse the command line arguments
    parsed_args = argument_parser_compute_position_error(script_name, sys.argv[1:])

    # initialize the logger
    logger = init_logger.logger_setup(args=parsed_args, base_name=script_name)

    logger.debug(f"Parsed arguments: {parsed_args}")

    # compute the position error
    compute_position_error(parsed_args=parsed_args, logger=logger)


if __name__ == "__main__":
    main()
