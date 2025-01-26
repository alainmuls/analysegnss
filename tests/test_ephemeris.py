import numpy as np
import pytest

from src.analysegnss.config import GPS_BDS_WEEK_DIFF
from src.analysegnss.gnss.GLONASSEphemeris import GLONASSEphemeris
from src.analysegnss.gnss.GNSSephemeris import GNSSEphemeris
from src.analysegnss.gnss.GNSSNavReader import GNSSNavReader
from src.analysegnss.config import R_EARTH
from src.analysegnss.gnss.gnss_dt import gnss2dt


# def test_read_gnss_nav_csv():
#     # Test data paths
#     nav_csv_fns = {
#         "GPS-LNAV": "tests/data/BERT00BEL_R_20243640700_41H_MN_GPS_LNAV.csv",
#         "GAL_INAV": "tests/data/BERT00BEL_R_20243640700_41H_MN_Galileo_INAV.csv",
#         "BDS_D1": "tests/data/BERT00BEL_R_20243640700_41H_MN_Beidou_D1.csv",
#         "BDS_D2": "tests/data/BERT00BEL_R_20243640700_41H_MN_Beidou_D2.csv",
#         "GPS-G16": "tests/data/BERT00BEL_R_20243640700_41H_MN_G16_GPS_LNAV.csv",
#     }

#     for nav_type, navcsv_fn in nav_csv_fns.items():
#         print(f"\nProcessing {nav_type} | {navcsv_fn}")
#         gnss_nav_reader = GNSSNavReader(csv_file=navcsv_fn)
#         gnss_nav_reader.read_GEC_nav_csv()
#         nav_data = gnss_nav_reader.get_ephemerides()

#         assert len(nav_data) > 0, f"No data read for {nav_type}"

#         # Test first ephemeris
#         eph = nav_data[0]

#         # print in tabular form
#         attributes = vars(eph)
#         items = sorted(attributes.items())
#         key_width = 12
#         val_width = 18

#         for i in range(0, len(items), 3):
#             row = items[i : i + 3]
#             line = ""
#             for attr, value in row:
#                 # line += f"{attr:>{key_width}} : {str(value):<{val_width}}"
#                 # line += f"{attr:>{key_width}} : {value} ({type(value).__name__}){' ':<{val_width-len(str(value))}}"

#                 # if isinstance(value, (int, float)):
#                 #     formatted_value = (
#                 #         f"{value:>{val_width}.12f}"
#                 #         if isinstance(value, float)
#                 #         else f"{value:>{val_width}d}"
#                 #     )
#                 # else:
#                 #     formatted_value = f"{str(value):<{val_width}}"

#                 if isinstance(value, float):
#                     formatted_value = f"{value:>{val_width}.9e}"
#                 elif isinstance(value, int):
#                     formatted_value = f"{value:>{val_width}d}"
#                 else:
#                     formatted_value = f"{str(value):<{val_width}}"

#                 line += f"{attr:>{key_width}} : {formatted_value}"
#             print(line)

#         assert eph is not None
#         assert hasattr(eph, "prn")
#         assert hasattr(eph, "health")


def test_satellite_position_calculation():
    # Test data paths
    nav_csv_fns = {
        # "GPS-LNAV": "tests/data/BERT00BEL_R_20243640700_41H_MN_GPS_LNAV.csv",
        # "GAL_INAV": "tests/data/BERT00BEL_R_20243640700_41H_MN_Galileo_INAV.csv",
        # "BDS_D1": "tests/data/BERT00BEL_R_20243640700_41H_MN_Beidou_D1.csv",
        # "BDS_D2": "tests/data/BERT00BEL_R_20243640700_41H_MN_Beidou_D2.csv",
        "GPS-G16": "tests/data/BERT00BEL_R_20243640700_41H_MN_G16_GPS_LNAV.csv",
    }
    # Test for each navigation type
    for nav_type, navcsv_fn in nav_csv_fns.items():
        gnss_nav_reader = GNSSNavReader(csv_file=navcsv_fn)
        gnss_nav_reader.read_GEC_nav_csv()
        nav_data = gnss_nav_reader.get_ephemerides()

        eph = nav_data[0]

        # Calculate positions at different times
        t = eph.toe
        WkNr = eph.week
        x, y, z = eph.compute_satellite_position(t)

        # Validate position values
        assert isinstance(x, (int, float))
        assert isinstance(y, (int, float))
        assert isinstance(z, (int, float))

        # Check reasonable orbital radius
        gnss_radius = np.sqrt(x**2 + y**2 + z**2)

        if nav_type.startswith("GPS-LNAV"):
            print(
                "\nNAV_TYPE     PRN  WKNR     TOW        X [m]           Y [m]           Z [m]    |     radius [m]  |     height [m]"
            )  # GPS orbital radius range in meters
        if not nav_type.startswith("BDS"):
            print(
                f"{nav_type:12s} {eph.prn:3d} {eph.week:5d} {t:7d} {x:15.3f} {y:15.3f} {z:15.3f} |"
                f" {gnss_radius:15.3f} | {gnss_radius - R_EARTH:15.3f}"
            )
        else:
            print(
                f"{nav_type:12s} {eph.prn:3d} {eph.week + GPS_BDS_WEEK_DIFF:5d} {t:7d} {x:15.3f} {y:15.3f} {z:15.3f} |"
                f" {gnss_radius:15.3f} | {gnss_radius - R_EARTH:15.3f}"
            )

        assert 20000000 < gnss_radius < 50000000  # GPS orbital radius range in meters

        if nav_type == "GPS-G16":
            pos_brdc = []
            pos_glab = []

            # read the corresponding GPS LNAV ephemeris from CSV file
            gnss_nav_reader = GNSSNavReader(csv_file=navcsv_fn)
            gnss_nav_reader.read_GEC_nav_csv()
            nav_data = gnss_nav_reader.get_ephemerides()

            t = eph.toe
            WkNr = eph.week

            # read all ines starting with SATPVT from the glab satpos file
            with open("tests/data/BERT00BEL_R_20243640700_41H_MN_G16.satpos", "r") as f:
                glab_lines = f.readlines()

            for t in range(eph.toe - 239 * 30, eph.toe + 240 * 30, 30):
                # convert the GPS Week/TOW to datetime
                dt = gnss2dt(week=WkNr, tow=t)
                x, y, z = eph.compute_satellite_position(t)

                pos_brdc.append((WkNr, eph.toe, eph.IODE, t, dt, x, y, z))
                # print(glab_hms, x, y, z)

                # search in glab_lines the lines that corresponds to the glab_hms
                glab_hms = dt.strftime("%H:%M:%S.%f")[:-4]
                for line in glab_lines:
                    if glab_hms in line:
                        # extract fields 10, 11 and 12
                        # print(line.split()[9])
                        # print(line.split()[9:12])
                        x_glab, y_glab, z_glab = map(float, line.split()[9:12])
                        glab_iode = int(line.split()[17])
                        pos_glab.append(
                            (WkNr, t, glab_iode, dt, glab_hms, x_glab, y_glab, z_glab)
                        )
                        break

            for i in range(len(pos_brdc)):
                dist_brdc = np.sqrt(
                    (pos_brdc[i][5] + pos_brdc[i][5]) ** 2
                    + (pos_brdc[i][6] + pos_brdc[i][6]) ** 2
                    + (pos_brdc[i][7] + pos_brdc[i][7]) ** 2
                )

                dist_glab = np.sqrt(
                    (pos_glab[i][5] + pos_glab[i][5]) ** 2
                    + (pos_glab[i][6] + pos_glab[i][6]) ** 2
                    + (pos_glab[i][7] + pos_glab[i][7]) ** 2
                )

                print(
                    f"{pos_brdc[i][0]:5d} {pos_brdc[i][1]:7d} | {pos_brdc[i][2]:3d} {pos_brdc[i][3]:6f} | "
                    f"{pos_brdc[i][4].strftime("%H:%M:%S.%f")[:-4]} | "
                    f" {pos_brdc[i][5]:15.3f} {pos_brdc[i][6]:15.3f} {pos_brdc[i][7]:15.3f}\n"
                    f"                {pos_glab[i][2]:3d}                 {pos_glab[i][3].strftime("%H:%M:%S.%f")[:-4]} | "
                    f" {pos_glab[i][5]:15.3f} {pos_glab[i][6]:15.3f} {pos_glab[i][7]:15.3f}"
                )

                assert np.isclose(dist_brdc, dist_glab, atol=1e-3)

            # # read file ./tests/data/BERT00BEL_R_20243640700_41H_MN_G16_GPS_LNAV.satpos
            # # find the line with timing 12:00:00.00 and extract the position
            # with open("tests/data/BERT00BEL_R_20243640700_41H_MN_G16.satpos", "r") as f:
            #     for line in f:
            #         if "12:00:00.00" in line:
            #             # extract fields 10, 11 and 12
            #             # print(line.split()[9])
            #             # print(line.split()[9:12])
            #             x_glab, y_glab, z_glab = map(float, line.split()[9:12])
            #             break
            #         else:
            #             continue

            #     print(
            #         f"\n{nav_type} {eph.prn} {WkNr} {t}: {x:15.3f} {y:15.3f} {z:15.3f}"
            #         f"\n                        {x_glab:15.3f} {y_glab:15.3f} {z_glab:15.3f}"
            #     )

            #     # assert that the difference between the _ref and _glab coordinates is less than 5mm
            #     assert abs(x_glab - x) < 0.005
            #     assert abs(y_glab - y) < 0.005
            #     assert abs(z_glab - z) < 0.005


# def test_glonass_ephemeris():
#     glonass_eph = GLONASSEphemeris()

#     # Test initial conditions
#     glonass_eph.x = 10000.0  # km
#     glonass_eph.y = 15000.0
#     glonass_eph.z = 20000.0
#     glonass_eph.vx = 1.0
#     glonass_eph.vy = 2.0
#     glonass_eph.vz = 3.0

#     # Test Runge-Kutta integration
#     t = 300  # 5 minutes
#     pos = glonass_eph.runge_kutta4(t)

#     # Validate position
#     assert len(pos) == 3
#     radius = np.sqrt(sum(p**2 for p in pos))
#     assert 19000 < radius < 26000  # GLONASS orbital radius range in km


if __name__ == "__main__":
    pytest.main([__file__])
