import pytest
import numpy as np
from src.analysegnss.gnss.GLONASSEphemeris import GLONASSEphemeris
from src.analysegnss.gnss.GNSSephemeris import GNSSEphemeris
from src.analysegnss.config import GPS_BDS_WEEK_DIFF


def test_read_nav_csv():
    # Test data paths
    nav_csv_fns = {
        "GPS-LNAV": "tests/data/BERT00BEL_R_20243640700_41H_MN_GPS_LNAV.csv",
        "GAL_INAV": "tests/data/BERT00BEL_R_20243640700_41H_MN_Galileo_INAV.csv",
        "BDS_D1": "tests/data/BERT00BEL_R_20243640700_41H_MN_Beidou_D1.csv",
        "BDS_D2": "tests/data/BERT00BEL_R_20243640700_41H_MN_Beidou_D2.csv",
    }

    for nav_type, file_path in nav_csv_fns.items():
        nav_data = read_nav_csv(file_path)
        assert len(nav_data) > 0, f"No data read for {nav_type}"

        # Test first ephemeris
        eph = nav_data[0]
        assert eph is not None
        assert hasattr(eph, "prn")
        assert hasattr(eph, "health")


def test_satellite_position_calculation():
    # Test for each navigation type
    nav_data = read_nav_csv("tests/data/BERT00BEL_R_20243640700_41H_MN_GPS_LNAV.csv")
    eph = nav_data[0]

    # Calculate positions at different times
    t = eph.toe
    x, y, z = eph.compute_satellite_position(t)

    # Validate position values
    assert isinstance(x, (int, float))
    assert isinstance(y, (int, float))
    assert isinstance(z, (int, float))

    # Check reasonable orbital radius
    radius = np.sqrt(x**2 + y**2 + z**2)
    assert 20000000 < radius < 30000000  # GPS orbital radius range in meters


def test_glonass_ephemeris():
    glonass_eph = GLONASSEphemeris()

    # Test initial conditions
    glonass_eph.x = 10000.0  # km
    glonass_eph.y = 15000.0
    glonass_eph.z = 20000.0
    glonass_eph.vx = 1.0
    glonass_eph.vy = 2.0
    glonass_eph.vz = 3.0

    # Test Runge-Kutta integration
    t = 300  # 5 minutes
    pos = glonass_eph.runge_kutta4(t)

    # Validate position
    assert len(pos) == 3
    radius = np.sqrt(sum(p**2 for p in pos))
    assert 19000 < radius < 26000  # GLONASS orbital radius range in km


if __name__ == "__main__":
    pytest.main([__file__])
