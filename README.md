# Repository for analyzing GNSS Data

The purpose of this repository is to provide a set of tools to analyze GNSS data or to extract data from GNSS data in a reusable way. GNSS data can come from different sources, such as:
- GNSS raw data from a GNSS receiver (SBF or u-Blox raw data)
- GNSS data from a GNSS simulator
- GNSS data from NMEA sentences
- GNSS data coming from a RTCM server
- processed GNSS data from software (RTKLib or gLab)

Using classes for each data source and commonly used functions, the GNSS data can be analyzed or used in a way that is reusable.

## Description

The repository contains Python scripts and Python classes for analyzing GNSS data. The repository is organized as follows:
- `sbf`: contains the classes for reading and parsing SBF files
- `rinex`: contains the classes for reading and parsing RINEX observation and navigation files
- `rtkpos`: contains the classes for reading and parsing the position and status files obtained by RTKLib processing
- `glab`: contains the classes for reading and parsing GLAB files (*not yet implemented*)
- `scripts`: contains `bash`scripts 

Each of these directories contain  Python classes for reading and parsing the data. The classes are designed to be used in a way that is reusable.

Next to these directories there is a `utils` directory which contains utility functions that can be used by Python scripts or the classes. The `gnss` directory contains at present the `geoid` directory which is used to calculate the geoid undulation $N$, so that orthometric height $H$ can be calculated from the ellipsoid height $h$. The `plot` directory contains functions for plotting GNSS data.


The repository contains the following classes:
- `sbf/sbf_class`: class for reading and parsing SBF files
- `rtkpos/rtkpos_class`: class for reading and parsing the position and status files obtained by RTKLib processing
- `rinex`:
  - `rinex_class`:  class containing common elements used by `rinex_obs_class` and `rinex_nav_class`
  - `rinex_obs_class`: class for reading and parsing RINEX observation files
  - `rinex_nav_class`: class for reading and parsing RINEX navigation files
- `glab/glab_class`: class for reading and parsing the gLAB files (*__not yet implemented__*)
- Other classes for reading and parsing data from other sources can be added similarly.

The main purpose is to create classes which are reusable for different contexts, whether it is for pure analysis, for monitoring purposes or for extracting GNSS data used for EBH (Equivalent Bump Height) calculations.

The design goal is to create Python scripts which follow the Linux principle of **"do one thing and do it well"**. Subsequent scripts can be used to call another script to further enhance the functionality. This is obtained by using the Python idiom `if __name__ == "__main__":`. This construct enables a single Python file to not only support reusable code and functions, but also contain executable code that will not explicitly run when a module is imported.

## Usage of Python logging class

See [Python logging class](./utils/readme.md).

## SBF related classes and functions

See [SBF related classes and functions](./sbf/readme.md).


## RTKPos related classes and functions

See [RTKPos related classes and functions](./rtkpos/readme.md).

## Contributing
State if you are open to contributions and what your requirements are for accepting them.

For people who want to make changes to your project, it's helpful to have some documentation on how to get started. Perhaps there is a script that they should run or some environment variables that they need to set. Make these steps explicit. These instructions could also be useful to your future self.

You can also document commands to lint the code or run tests. These steps help to ensure high code quality and reduce the likelihood that the changes inadvertently break something. Having instructions for running tests is especially helpful if it requires external setup, such as starting a Selenium server for testing in a browser.

## Authors and acknowledgment

- Alain MULS
