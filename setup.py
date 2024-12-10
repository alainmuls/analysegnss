from setuptools import setup, find_packages

setup(
    name="analysegnss",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": [
            "rtk_pvtgeod=analysegnss.sbf.rtk_pvtgeod:main",
            "ppk_rnx2rtkp=analysegnss.rtkpos.ppk_rnx2rtkp:main",
            "ebh_lines=analysegnss.scripts.ebh.ebh_lines:main",
            "rtkppk_plot=analysegnss.plots.rtkppk_plot:main",
            "rnx_csv=analysegnss.rinex.rnx_csv:main",
            "rnxobs_csv=analysegnss.rinex.rnxobs_csv:main",
            "rnxnav_csv=analysegnss.rinex.rnxnav_csv:main",
        ]
    },
)
