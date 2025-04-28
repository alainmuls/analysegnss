#! /usr/bin/env python

# standard library imports
import os
import sys

# third party imports
import numpy as np


def euclidean_distance(
    x1: float,
    x2: float,
    y1: float,
    y2: float,
    z1: float | None = None,
    z2: float | None = None,
) -> float:
    """
    Calculate the euclidean distance between two coordinates in 2D or 3D space.
    # TODO: add this function to the utils.utilities.py file?
    args:
    x1 (float): x coordinate of the first point
    y1 (float): y coordinate of the first point
    z1 (float): z coordinate of the first point
    x2 (float): x coordinate of the second point
    y2 (float): y coordinate of the second point
    z2 (float): z coordinate of the second point

    returns:
    distance (float): euclidean distance between two coordinates
    """

    if z1 is None or z2 is None:
        return np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    else:
        return np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)
