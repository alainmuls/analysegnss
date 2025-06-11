# Repository for analyzing GNSS Data

The purpose of this repository is to provide a set of tools to analyze GNSS data or to extract data from GNSS data in a reusable way. GNSS data can come from different sources, such as:
- GNSS raw data from a GNSS receiver (SBF or u-Blox raw data)
- GNSS data from a GNSS simulator
- GNSS data from NMEA sentences
- GNSS data coming from a RTCM server
- processed GNSS data from software (RTKLib or gLab)

Using classes for each data source and commonly used functions, the GNSS data can be analyzed or used in a way that is reusable.

## Description

The repository contains Python scripts and Python classes for analyzing and visualizing GNSS data. The repository contains directories for each of the following data sources:
- `sbf`: contains the classes for reading and parsing SBF files
- `rinex`: contains the classes for reading and parsing RINEX observation and navigation files
- `rtkpos`: contains the classes for reading and parsing the position and status files obtained by RTKLib processing
- `ublox`: contains the classes for reading and parsing u-Blox raw files
- `glabng`: contains the classes for reading and parsing gLAB v6.0 (or gLABng) files
- `gnss`: contains specific GNSS related functions
- `plots`: contains functions for plotting GNSS data
- `utils`: contains utility functions
- `scripts`: contains `bash`scripts 

Each of these directories contain Python classes or functions for reading, parsing, plotting or perform analysis of GNSS data. These classes and scripts are designed to be used in a reusable way.

## Classes

The repository contains the following classes:
- `sbf/sbf_class`: class for reading and parsing SBF files
- `rtkpos/rtkpos_class`: class for reading and parsing the position and status files obtained by RTKLib processing
- `rinex`:
  - `rinex_class`:  class containing common elements used by `rinex_obs_class` and `rinex_nav_class`
  - `rinex_obs_class`: class for reading and parsing RINEX observation files
  - `rinex_nav_class`: class for reading and parsing RINEX navigation files
- `ublox`:
  - `ublox_class`: class for reading and parsing u-Blox raw files
  - `ubx_mga_gps_nav.py`: class that decodes ephemeris parameters 
  - `ubx_nav_dop.py`: class that extracts Dilution of Precision (DOP) values
  - `ubx_nav_posllh.py`: class that decodes geodetic position 
  - `ubx_nav_pvt.py`: class that extracts a comprehensive set of navigation solution data 
  - `ubx_nav_relposned.py`: class that decodes relative positioning information in North-East-Down (NED) frame
  - `ubx_nav_sat.py`: class that extracts detailed information for each visible satellite
  - `ubx_rxm_rawx.py`: class that decodes raw measurement data for each satellite signal 
- `glabng/glabng_class`: class for reading and parsing the gLABng files
- Other classes for reading and parsing data from other sources will be added similarly.

The main purpose is to create classes and functions which are reusable for different contexts, whether it is for pure analysis, for monitoring purposes or for extracting GNSS data used for EBH (Equivalent Bump Height) calculations.

The design goal is to create Python scripts which follow the Linux principle of **"do one thing and do it well"**. Subsequent scripts can be used to call another script, using the output of the called script to further enhance the functionality. This is obtained by using the Python idiom `if __name__ == "__main__":`. This construct enables a single Python file to not only support reusable code and functions, but also contain executable code that will not explicitly run when a module is imported.

### Usage of Python logging class

See [Python logging class](./src/analysegnss/utils/readme.md).

### SBF related classes and functions

See [SBF related classes and functions](./src/analysegnss/sbf/readme.md).

### u-Blox related classes and functions

See [u-Blox related classes and functions](./src/analysegnss/ublox/readme.md).


### RTKPos related classes and functions

See [RTKPos related classes and functions](./src/analysegnss/rtkpos/readme.md).

### GLABNG related classes and functions

See [GLABNG related classes and functions](./src/analysegnss/glabng/readme.md).

### PLOT scripts

See [PLOT scripts](./src/analysegnss/plots/readme.md).

## Contributing
State if you are open to contributions and what your requirements are for accepting them.

For people who want to make changes to your project, it's helpful to have some documentation on how to get started. Perhaps there is a script that they should run or some environment variables that they need to set. Make these steps explicit. These instructions could also be useful to your future self.

You can also document commands to lint the code or run tests. These steps help to ensure high code quality and reduce the likelihood that the changes inadvertently break something. Having instructions for running tests is especially helpful if it requires external setup, such as starting a Selenium server for testing in a browser.

## Authors and acknowledgment

- Alain MULS
- Pieterjan DE MEULEMEESTER 

## License
For open source projects, say how it is licensed.

