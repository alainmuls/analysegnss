import sys
import numpy as np
import pytest
from rich import print as rprint

from src.analysegnss.config import GPS_BDS_WEEK_DIFF

from src.analysegnss.gnss.gnss_nav_reader import GNSSNavReader
from src.analysegnss.gnss.gnss_dt import gnss2dt
from src.analysegnss.config import ERROR_CODES


def test_read_gnss_nav_csv():
    # Test data paths
    nav_csv_fns = {
        "GPS-LNAV": "tests/data/BERT00BEL_R_20243640700_41H_MN_GPS_LNAV.csv",
        "GAL_INAV": "tests/data/BERT00BEL_R_20243640700_41H_MN_Galileo_INAV.csv",
        "BDS_D1": "tests/data/BERT00BEL_R_20243640700_41H_MN_Beidou_D1.csv",
        "BDS_D2": "tests/data/BERT00BEL_R_20243640700_41H_MN_Beidou_D2.csv",
        "GPS-G16": "tests/data/BERT00BEL_R_20243640700_41H_MN_G16_GPS_LNAV.csv",
    }

    for nav_type, navcsv_fn in nav_csv_fns.items():
        print(f"\nProcessing {nav_type} | {navcsv_fn}")
        gnss_nav_reader = GNSSNavReader(csv_file=navcsv_fn)
        gnss_nav_reader.read_GEC_nav_csv()
        nav_data = gnss_nav_reader.get_all_ephemeris()

        assert len(nav_data) > 0, f"No data read for {nav_type}"

        # Test first ephemeris
        eph = nav_data[0]

        # print in tabular form
        attributes = vars(eph)
        items = sorted(attributes.items())
        key_width = 12
        val_width = 18

        for i in range(0, len(items), 3):
            row = items[i : i + 3]
            line = ""
            for attr, value in row:
                if isinstance(value, float):
                    formatted_value = f"{value:>{val_width}.9e}"
                elif isinstance(value, int):
                    formatted_value = f"{value:>{val_width}d}"
                else:
                    formatted_value = f"{str(value):<{val_width}}"

                line += f"{attr:>{key_width}} : {formatted_value}"
            print(line)

        assert eph is not None
        assert hasattr(eph, "prn")
        assert hasattr(eph, "health")


def test_satellite_position_calculation():
    # Test data paths
    data_infos = {
        "GPS-G16": {
            "cvs_ifn": "tests/data/BERT00BEL_R_20243640700_41H_MN_G16_GPS_LNAV.csv",
            "t_mid": 128580,
            "satpos_ifn": "tests/data/BERT00BEL_R_20243640700_41H_MN_G16.satpos",
        },
        "BDS-C14": {
            "cvs_ifn": "tests/data/BERT00BEL_R_20243640700_41H_MN_C14_Beidou_D2.csv",
            "t_mid": 105000,
            "satpos_ifn": "tests/data/BERT00BEL_R_20243640700_41H_MN_C14.satpos",
        },
    }

    # Test for each navigation type
    print(data_infos)
    print(data_infos.keys())
    print(data_infos.values())
    for gnss_prn, data_info in data_infos.items():
        print(f"\nProcessing {gnss_prn}")
        print(f"  Processing {data_info.keys()}")
        print(f"  Processing {data_info.values()}")
        cvs_ifn = data_info["cvs_ifn"]
        t_mid = data_info["t_mid"]
        satpos_ifn = data_info["satpos_ifn"]
        print(f"  Processing {cvs_ifn} | {t_mid} | {satpos_ifn}")

        gnss_nav_reader = GNSSNavReader(csv_file=cvs_ifn)
        gnss_nav_reader.read_GEC_nav_csv()

        pos_brdc = []
        pos_glab = []

        # current time t
        t_mid = (t_mid // 30) * 30

        # read all ines starting with SATPOS from the glab satpos file
        with open(satpos_ifn, "r") as f:
            glab_lines = f.readlines()
        # print(glab_lines)

        for t_cur in range(t_mid - 239 * 30, t_mid + 240 * 30, 600):
            # convert the GPS Week/TOW to datetime
            eph = gnss_nav_reader.get_ephemeris(t=t_cur)
            if gnss_prn == "BDS-C14":
                WkNr = eph.week + GPS_BDS_WEEK_DIFF
            else:
                WkNr = eph.week

            dt = gnss2dt(week=WkNr, tow=t_cur)
            try:
                x, y, z = eph.calculate_GPS_GAL_coordinates(t=t_cur)
                pos_brdc.append((WkNr, eph.toe, eph.IODE, t_cur, dt, x, y, z))
            except ValueError as e:
                print(e)
                sys.exit(ERROR_CODES["E_WRONG_GNSS"])

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
                        (
                            WkNr,
                            t_cur,
                            glab_iode,
                            dt,
                            glab_hms,
                            x_glab,
                            y_glab,
                            z_glab,
                        )
                    )
                    break

        print("=" * 80)
        print(f"len(pos_brdc) = {len(pos_brdc)}")
        print(f"pos_brdc[:1]: {pos_brdc[:1]}")
        print(f"pos_brdc[-1:]: {pos_brdc[-1:]}")

        print("-" * 80)
        print(f"len(pos_glab) = {len(pos_glab)}")
        print(f"pos_glab[:1]: {pos_glab[:1]}")
        print(f"pos_glab[-1:]: {pos_glab[-1:]}")
        print("-" * 80)

        for i in range(len(pos_brdc)):
            dist_brdc = np.sqrt(
                pos_brdc[i][5] ** 2 + pos_brdc[i][6] ** 2 + pos_brdc[i][7] ** 2
            )


            dist_glab = np.sqrt(
                pos_glab[i][5] ** 2 + pos_glab[i][6] ** 2 + pos_glab[i][7] ** 2
            )

            print(
                f"{pos_brdc[i][0]:5d} {pos_brdc[i][1]:7d} | {pos_brdc[i][2]:3d} {pos_brdc[i][3]:6.0f} | "
                f"{pos_brdc[i][4].strftime("%H:%M:%S.%f")[:-4]} | "
                f" {pos_brdc[i][5]:15.3f} {pos_brdc[i][6]:15.3f} {pos_brdc[i][7]:15.3f} | {dist_brdc:15.3f}\n"
                f"                {pos_glab[i][2]:3d}          {pos_glab[i][3].strftime("%H:%M:%S.%f")[:-4]} | "
                f" {pos_glab[i][5]:15.3f} {pos_glab[i][6]:15.3f} {pos_glab[i][7]:15.3f} | {dist_glab:15.3f}\n"
                f"                                            "
                f"{pos_brdc[i][5] - pos_glab[i][5]:15.3f} {pos_brdc[i][6] - pos_glab[i][6]:15.3f} "
                f"{pos_brdc[i][7] - pos_glab[i][7]:15.3f} | {dist_brdc - dist_glab:15.3f}"
            )

            assert np.isclose(dist_brdc, dist_glab, atol=1e-9)

        print("#" * 80)


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
