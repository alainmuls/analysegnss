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
- `rtkpos`: contains the classes for reading and parsing the position and status files obtained by RTKLib processing
- `glab`: contains the classes for reading and parsing GLAB files (*not yet implemented*)

Each of these directories contain a Python class for reading and parsing the data. The classes are designed to be used in a way that is reusable.

Next to these directories there is a `utils` directory which contains utility functions that can be used by Python scripts or the classes. The `gnss` directory contains at present the `geoid` directory which is used to calculate the geoid height $H$ from the ellipsoid height $h$ and the geoid undulation $N$. The `plot` directory contains functions for plotting GNSS data.


The repository contains the following classes:
- `sbf/sbf_class`: class for reading and parsing SBF files
- `rtkpos/rtkpos_class`: class for reading and parsing the position and status files obtained by RTKLib processing
- `glab/glab_class`: class for reading and parsing the GLAB files (*__not yet implemented__*)
- Other classes for reading and parsing data from other sources can be added in a similar fashion.

The main purpose is to create classes which are reusable for different contexts, whether it is for pure analysis, for monitoring purposes or for extracting GNSS data used for EBH calculations.

The design goal is to create Python scripts which follow the Linux principle of **"do one thing and do it well"**. Subsequent scripts can be used to call another script to further enhance the functionality. This is obtained by using the Python idiom `if __name__ == "__main__":`. This construct enables a single Python file to not only support reusable code and functions, but also contain executable code that will not explicitly run when a module is imported.

## Usage of Python logging class
The Python logging class is used to log messages to a file and to the console. The logger methods are named after the level or severity of the events they are used to tracking. The standard levels and their applicability are described below (in increasing order of severity):

| Level    | When it’s used                                                                                                                                                         |
| -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| DEBUG    | Detailed information, typically of interest only when diagnosing problems.                                                                                             |
| INFO     | Confirmation that things are working as expected.                                                                                                                      |
| WARNING  | An indication that something unexpected happened, or indicative of some problem in the near future (e.g. ‘disk space low’). The software is still working as expected. |
| ERROR    | Due to a more serious problem, the software has not been able to perform some function.                                                                                |
| CRITICAL | A serious error, indicating that the program itself may be unable to continue running.                                                                                 |


 The implemented logger class creates logger objects which are used in the following way:
- the file logger logs all messages equal or higher than `DEBUG` and writes them to a file named `script_name.log` in the `logs` directory in daily files.
- the console logger logs all messages equal or higher defined by the option `--verbose` or `-v`:
  - `-v`: logs all messages equal or higher than `WARNING`
  - `-vv`: logs all messages equal or higher than `INFO`
  - `-vvv`: logs all messages equal or higher than `DEBUG`.


## The `argparse` module

The CLI arguments are parsed using the `argparse` module. The `argparse` module is a standard library module in Python that provides a way to parse command-line arguments. In order to assist the user in finding out which arguments are available, the `argparse` module provides a help message that lists all the available arguments.

```bash
± rtk_pvtgeod.py -h
usage: rtk_pvtgeod.py [-h] [-V] [-v] --sbf_fn SBF_FN

argument_parser.py analysis of SBF data

options:
  -h, --help       show this help message and exit
  -V, --version    show program's version number and exit
  -v, --verbose    verbose level... repeat up to three times.
  --sbf_fn SBF_FN  input SBF filename
```

By importing the `argcomplete` module, the command line arguments can be completed automatically by pressing the tab key after including in the `~/.bashrc` file:

```bash
for file in  rtk_pvtgeod.py ppk_rnx2rtkp.py rtkppk_plot.py ebh_lines.py
do
    complete -o nospace -o default -o bashdefault -F _Python_argcomplete ${file}
done
```

The file `utils/argument_parser.py` contains the function `argument_parser_xyz()` which is used to parse the command line arguments for each Python script. The function `argument_parser_xyz()` is called in the main script and the arguments are passed to the main function. 

## SBF related classes and functions

The `sbf_class` is a class that reads and parses SBF files. The class  has the following fields:
- `sbf_fn`: the SBF filename, mandatory
- `start_time`: the start time of the SBF file, optional
- `end_time`: the end time of the SBF file, optional
- `logger`: the logger object, optional

During initialization of the class, the fields (except `logger`) are validated.

The class has the following methods:
- `def bin2asc_dataframe(self, lst_sbfblocks: list) -> dict:`
    This method converts the SBF data to a dictionary of [polars dataframes](https://docs.pola.rs/)  using the `bin2asc` method. The dictionary contains as keys the SBF block names and as values the [polars dataframes](https://docs.pola.rs/). Its purpose is to convert the SBF data to a dictionary of [polars dataframes](https://docs.pola.rs/) by only parsing ones the SBF file `sbf_fn`. The call to `bin2asc` has always the options "-f", `self.sbf_fn`, "-n", "NaN", "-E", "-r", "-t", "-v" and adds one or several `-m` option followed by the SBF block name.
    
    `bin2asc` is a command line tool that converts binary SBF files to CSV files and is part of the  [Septentrio RxTools](https://www.septentrio.com/en/products/software/rxtools#resources) software.

- `def add_columns(self, block_df: pl.DataFrame) -> pl.DataFrame:`
    Depending on the converted SBF block some additional columns are created for later use. 
    - `"WNc [w]", "TOW [0.001 s]"` are converted to a Python `datetime` object.
    - `"SVID"` is converted to a `"PRN"` string.
      - _Remark: the `"SVID"` field should be an integer but sometimes it is a string which is a bug in the `bin2asc` conversion._
    - `"Latitude [rad]", "Longitude [rad]"` are converted to `"Latitude [deg]"` and `"Longitude [deg]"` and to `"UTM.E", "UTM.N"` using the `utm` module. The geodetic coordinates in radians are subsequently dropped.
    - `"Height [m]", "Undulation [m]"` are combined to `"ortoH [m]"`.

- `def used_columns(self, sbf_block: str) -> list:`
    The `bin2asc` conversion creates CSV files with a lot of information which are not all needed. This method selects the columns used for the subsequent analysis or processing. The columns are selected based on the SBF block name and the `dtype` of the column is set to the [polars](https://docs.pola.rs/) type definition, reducing the memory usage of the SBF block [polars dataframe](https://docs.pola.rs/).
        - _Remark: currently only implemented for the `PVTGeodetic2` SBF block._

In the `sbf` directory the file `sbf_constants.py` contains the constants used for interpreting some of the SBF data fields. 

## RTKPos related classes and functions

A similar setup is used for the `RTKPos` class. The class has the following fields:
- `pos_fn`: the SBF filename, mandatory
- `start_time`: the start time of the SBF file, optional
- `end_time`: the end time of the SBF file, optional
- `logger`: the logger object, optional

    - _Remark: for using the RTKLib created position file with the [polars dataframe](https://docs.pola.rs/) the position file has to be created with the `-s sep :   field separator [' ']` option to obtain a CSV file._

The class has the following methods:
- `def rtkpos_schema(self) -> dict:`
    This method returns a dictionary with the column names and the [polars](https://docs.pola.rs/) dtypes for the columns found in the RTKPos CSV position file, reducing the memory usage of the  [polars dataframe](https://docs.pola.rs/).

- `def info_processing(self) -> Tuple[dict, list]:`
    This method returns a tuple containing:
        - a dictionary with the processing information extracted from the RTKPos CSV position file (cfr extract below)
        - a list containing the column names of the RTKPos CSV position file, by replacing the `"GPST"` column name with `"WNc", "TOW(s)"`.
```bash
% program   : rnx2rtkp ver.demo5 b34g
% inp file  : rnx/ROVR00BEL_R_20241701647_05H_10Z_MO.rnx
% inp file  : rnx/SSEA00XXX_R_20241701639_05H_01S_MO.rnx
% inp file  : rnx/SSEA00XXX_R_20241701620_06H_MN.rnx
% obs start : 2024/06/18 16:47:43.0 GPST (week2319 233263.0s)
% obs end   : 2024/06/18 21:03:43.1 GPST (week2319 248623.1s)
% ref pos   : 33.241210525,-115.951228361,  -66.0251
%
% (lat/lon/height=WGS84/ellipsoidal,Q=1:fix,2:float,3:sbas,4:dgps,5:single,6:ppp,ns=# of satellites)
%  GPST      , latitude(deg),longitude(deg), height(m),  Q, ns,  sdn(m),  sde(m),  sdu(m), sdne(m), sdeu(m), sdun(m),age(s), ratio
```

- `def add_columns(self, df_pos: pl.DataFrame) -> pl.DataFrame:`    
    Similar to the `add_columns` method of the `Sbf` class, but for the RTKPos CSV position file.

## Python scripts with a main function

### The script `rtk_pvtgeod.py`

```bash
± rtk_pvtgeod.py -h
usage: rtk_pvtgeod.py [-h] [-V] [-v] --sbf_fn SBF_FN

argument_parser.py analysis of SBF data

options:
  -h, --help       show this help message and exit
  -V, --version    show program's version number and exit
  -v, --verbose    verbose level... repeat up to three times.
  --sbf_fn SBF_FN  input SBF filename
```
This script reads the SBF file and extracts the PVTGeodetic2 block and writes the data to  [polars dataframe](https://docs.pola.rs/) with selected columns.

```bash
± rtk_pvtgeod.py --sbf_fn ./data/1342172Z.24_ -vv
2024-08-05 14:22:28,510 [INFO](rtk_pvtgeod:init_logger.pylogger_setup:78): ---------- start rtk_pvtgeod -------------
2024-08-05 14:22:28,511 [INFO](rtk_pvtgeod:rtk_pvtgeod.pyrtk_pvtgeod:67): Parsed arguments: Namespace(verbose=2, sbf_fn='./data/1342172Z.24_')
2024-08-05 14:22:28,511 [INFO](rtk_pvtgeod:sbf_class.pyvalidate_file:50): File validated successfully: ./data/1342172Z.24_
self.start_time = None
2024-08-05 14:22:28,511 [INFO](rtk_pvtgeod:sbf_class.pyvalidate_start_time:67): No start time specified.
self.end_time = None
2024-08-05 14:22:28,511 [INFO](rtk_pvtgeod:sbf_class.pyvalidate_end_time:82): No end time specified.
2024-08-05 14:22:28,511 [INFO](rtk_pvtgeod:sbf_class.pybin2asc_dataframe:101): /opt/Septentrio/RxTools/bin/bin2asc conversion of SBF file ./data/1342172Z.24_ to CSV files and importing into dataframes for SBF blocks
PVTGeodetic2
Verbose mode
Display of raw values enabled
Input file: ./data/1342172Z.24_
Assuming default format: SBF
Selected messages: PVTGeodetic2
DoNotUse representation: NaN
Column titles enabled
Messages without valid time are excluded
Processing file ./data/1342172Z.24_
Errors occurred during decoding of data (see output files).                     
Duration: 10.563 seconds.
{'Latitude [rad]': Float64, 'Longitude [rad]': Float64, 'Height [m]': Float64, 'Undulation [m]': Float32, 'COG [°]': Float32, 'TOW [0.001 s]': UInt32, 'SignalInfo': UInt32, 'WNc [w]': UInt16, 'MeanCorrAge [0.01 s]': UInt16, 'Type': UInt8, 'Error': UInt8, 'NrSV': UInt8}
2024-08-05 14:22:39,315 [INFO](rtk_pvtgeod:sbf_class.pyadd_columns:186): 	removing rows with no PVT solution
2024-08-05 14:22:39,318 [INFO](rtk_pvtgeod:sbf_class.pyadd_columns:192): 	adding datetime column to the dataframe
2024-08-05 14:22:39,325 [INFO](rtk_pvtgeod:sbf_class.pyadd_columns:218): 	adding UTM coordinates to the dataframe
2024-08-05 14:22:39,328 [INFO](rtk_pvtgeod:sbf_class.pyadd_columns:267): 	adding orthometric height to the dataframe
2024-08-05 14:22:39,330 [WARNING](rtk_pvtgeod:sbf_class.pyadd_columns:274): 	collecting the dataframe. Be patient.

Analysis of the quality of the position data
2024-08-05 14:22:46,051 [WARNING](rtk_pvtgeod:rtk_pvtgeod.pyquality_analysis:40): ╒═══════════════════════════╤═════════╤══════════════╕
│ PNT Mode                  │   Count │ Percentage   │
╞═══════════════════════════╪═════════╪══════════════╡
│ RTK with ﬁxed ambiguities │  114423 │ 82.50%       │
│ Stand-Alone PVT           │   12522 │ 9.03%        │
│ Differential PVT          │    5945 │ 4.29%        │
│ RTK with ﬂoat ambiguities │    5809 │ 4.19%        │
╘═══════════════════════════╧═════════╧══════════════╛
shape: (138_699, 16)
┌───────────────┬─────────┬──────┬───────┬────────────┬────────────────┬─────────┬──────┬──────────────────────┬────────────┬─────────────────────────┬────────────────┬─────────────────┬───────────────┬──────────┬────────┐
│ TOW [0.001 s] ┆ WNc [w] ┆ Type ┆ Error ┆ Height [m] ┆ Undulation [m] ┆ COG [°] ┆ NrSV ┆ MeanCorrAge [0.01 s] ┆ SignalInfo ┆ DT                      ┆ latitude [deg] ┆ longitude [deg] ┆ UTM.E         ┆ UTM.N    ┆ orthoH │
│ ---           ┆ ---     ┆ ---  ┆ ---   ┆ ---        ┆ ---            ┆ ---     ┆ ---  ┆ ---                  ┆ ---        ┆ ---                     ┆ ---            ┆ ---             ┆ ---           ┆ ---      ┆ ---    │
│ u32           ┆ u16     ┆ u8   ┆ u8    ┆ f64        ┆ f32            ┆ f32     ┆ u8   ┆ u16                  ┆ u32        ┆ datetime[μs]            ┆ f64            ┆ f64             ┆ f64           ┆ f64      ┆ f64    │
╞═══════════════╪═════════╪══════╪═══════╪════════════╪════════════════╪═════════╪══════╪══════════════════════╪════════════╪═════════════════════════╪════════════════╪═════════════════╪═══════════════╪══════════╪════════╡
│ 397836600     ┆ 2319    ┆ 1    ┆ 0     ┆ 10.806     ┆ -33.362        ┆ null    ┆ 5    ┆ null                 ┆ 131072     ┆ 2024-06-20 14:30:36.600 ┆ 33.147268      ┆ -116.130561     ┆ 581085.395441 ┆ 3.6679e6 ┆ 44.168 │
│ 397836700     ┆ 2319    ┆ 1    ┆ 0     ┆ 10.801     ┆ -33.362        ┆ null    ┆ 5    ┆ null                 ┆ 131072     ┆ 2024-06-20 14:30:36.700 ┆ 33.147268      ┆ -116.130561     ┆ 581085.394853 ┆ 3.6679e6 ┆ 44.163 │
│ 397836800     ┆ 2319    ┆ 1    ┆ 0     ┆ 10.797     ┆ -33.362        ┆ null    ┆ 5    ┆ null                 ┆ 131072     ┆ 2024-06-20 14:30:36.800 ┆ 33.147268      ┆ -116.130561     ┆ 581085.397961 ┆ 3.6679e6 ┆ 44.159 │
│ 397836900     ┆ 2319    ┆ 1    ┆ 0     ┆ 10.802     ┆ -33.362        ┆ null    ┆ 5    ┆ null                 ┆ 131072     ┆ 2024-06-20 14:30:36.900 ┆ 33.147268      ┆ -116.130561     ┆ 581085.399075 ┆ 3.6679e6 ┆ 44.164 │
│ 397837000     ┆ 2319    ┆ 1    ┆ 0     ┆ 10.798     ┆ -33.362        ┆ null    ┆ 5    ┆ null                 ┆ 131072     ┆ 2024-06-20 14:30:37     ┆ 33.147268      ┆ -116.130561     ┆ 581085.398812 ┆ 3.6679e6 ┆ 44.16  │
│ …             ┆ …       ┆ …    ┆ …     ┆ …          ┆ …              ┆ …       ┆ …    ┆ …                    ┆ …          ┆ …                       ┆ …              ┆ …               ┆ …             ┆ …        ┆ …      │
│ 412243600     ┆ 2319    ┆ 1    ┆ 0     ┆ 6.731      ┆ -33.355        ┆ null    ┆ 25   ┆ null                 ┆ 1881300997 ┆ 2024-06-20 18:30:43.600 ┆ 33.153778      ┆ -116.136138     ┆ 580559.374515 ┆ 3.6687e6 ┆ 40.086 │
│ 412243700     ┆ 2319    ┆ 1    ┆ 0     ┆ 6.72       ┆ -33.355        ┆ null    ┆ 25   ┆ null                 ┆ 1881300997 ┆ 2024-06-20 18:30:43.700 ┆ 33.153778      ┆ -116.136138     ┆ 580559.377845 ┆ 3.6687e6 ┆ 40.075 │
│ 412243800     ┆ 2319    ┆ 1    ┆ 0     ┆ 6.71       ┆ -33.355        ┆ null    ┆ 25   ┆ null                 ┆ 1881300997 ┆ 2024-06-20 18:30:43.800 ┆ 33.153778      ┆ -116.136138     ┆ 580559.380503 ┆ 3.6687e6 ┆ 40.065 │
│ 412243900     ┆ 2319    ┆ 1    ┆ 0     ┆ 6.701      ┆ -33.355        ┆ null    ┆ 25   ┆ null                 ┆ 1881300997 ┆ 2024-06-20 18:30:43.900 ┆ 33.153778      ┆ -116.136138     ┆ 580559.383026 ┆ 3.6687e6 ┆ 40.056 │
│ 412244000     ┆ 2319    ┆ 1    ┆ 0     ┆ 6.687      ┆ -33.355        ┆ null    ┆ 25   ┆ null                 ┆ 1881300997 ┆ 2024-06-20 18:30:44     ┆ 33.153778      ┆ -116.136138     ┆ 580559.38578  ┆ 3.6687e6 ┆ 40.042 │
└───────────────┴─────────┴──────┴───────┴────────────┴────────────────┴─────────┴──────┴──────────────────────┴────────────┴─────────────────────────┴────────────────┴─────────────────┴───────────────┴──────────┴────────┘
```

The created polars dataframe is returned and can thus be used by another script which calls this script.


## Roadmap
If you have ideas for releases in the future, it is a good idea to list them in the README.

## Contributing
State if you are open to contributions and what your requirements are for accepting them.

For people who want to make changes to your project, it's helpful to have some documentation on how to get started. Perhaps there is a script that they should run or some environment variables that they need to set. Make these steps explicit. These instructions could also be useful to your future self.

You can also document commands to lint the code or run tests. These steps help to ensure high code quality and reduce the likelihood that the changes inadvertently break something. Having instructions for running tests is especially helpful if it requires external setup, such as starting a Selenium server for testing in a browser.

## Authors and acknowledgment
Show your appreciation to those who have contributed to the project.

## License
For open source projects, say how it is licensed.

## Project status
If you have run out of energy or time for your project, put a note at the top of the README saying that development has slowed down or stopped completely. Someone may choose to fork your project or volunteer to step in as a maintainer or owner, allowing your project to keep going. You can also make an explicit request for maintainers.
