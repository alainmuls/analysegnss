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
        ]
    },
)
