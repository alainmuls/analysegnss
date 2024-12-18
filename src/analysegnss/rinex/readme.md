
## RINEX related classes and functions

### The class `RINEX`

The `RINEX` class is a base class for the `RINEX_OBS` and `RINEX_NAV` classes. The class has the following fields:
- `gnss`: for selecting the GNSS (GPS, GLONASS, Galileo, BeiDou))
- `start_time`: the start time, optional
- `end_time`: the end time, optional
- `logger`: the logger object, optional

### The class `RINEX_OBS`

The `RINEX_OBS` class is used to read and parse the RINEX observation files. The class adds the following fields:
- `rnxobs_fn`: the RINEX observation filename, mandatory

    and has the following methods:

    - `def validate_rnxobs_fn(self):` which checks if the RINEX observation file is valid and corresponds to an observation file.
    - `def gfzrnx_tabobs(self) -> dict:` which returns a dictionary with the observation types and their corresponding values per GNSS in the RINEX observation file using the `gfzrnx` executable and creates a tabular representation of the observation types.
    - `def tabobs_to_csv(self, result_dfs: dict) -> pl.DataFrame:` which converts the dictionary of dataframes obtained from the `gfzrnx_tabobs` method into a single dataframe and saves it to a CSV file. The CSV file contains the following columns: `GNSS,WKNR,TOW,PRN,cfreq,sigt,C,L,D,S`

### The class `RINEX_NAV`

The `RINEX_NAV` class is used to read and parse the RINEX navigation files. The class adds the following fields:
- `rnxnav_fn`: the RINEX navigation filename, mandatory

    and has the following methods:
    - `def validate_rnxnav_fn(self):` which checks if the RINEX navigation file is valid and corresponds to a navigation file.
    - `def gfzrnx_tabnav(self) -> dict:` which returns a dictionary with the navigation types and their corresponding values per GNSS in the RINEX navigation file using the `gfzrnx` executable and creates a tabular representation of the navigation types in a CSV file.

## The scripts `rnxobs_csv.py`, `rnxnav_csv.py` and `rnx_csv.py`

```bash
± rnxobs_csv -h
usage: rnxobs_csv [-h] [-V] [-v] --obs_fn OBS_FN [--csv_fn CSV_FN] [--gnss GNSS]

argument_parser.py Convert RINEX observation file to CSV file similar to those created by rtcm3_parser.py

options:
  -h, --help       show this help message and exit
  -V, --version    show program's version number and exit
  -v, --verbose    verbose level... repeat up to three times.
  --obs_fn OBS_FN  RINEX observation filename
  --csv_fn CSV_FN  CSV observation filename (defaults to filename with extension csv)
  --gnss GNSS      GNSS systems to convert (default: GE, select between G, R, E, C)
```
generates the output:
```text
<GNSS,WKNR,TOW,PRN,cfreq,sigt,C,L,D,S
E,2334,210120000,10,L1,1C,19911619.838,104636267.87,1274.572,44.0
E,2334,210120000,10,L5,5Q,19911628.081,78137504.342,951.712,48.0
E,2334,210120000,10,L7,7Q,19911626.607,80175869.498,976.588,46.0
E,2334,210120000,10,L8,8Q,19911627.161,79156686.461,964.146,50.0
E,2334,210120000,12,L1,1C,19123858.548,100496554.762,-105.532,43.0
E,2334,210120000,12,L5,5Q,19123863.411,75046147.55,-78.771,45.0
E,2334,210120000,12,L7,7Q,19123862.191,77003868.615,-80.862,43.0
E,2334,210120000,12,L8,8Q,19123862.642,76025010.624,-79.814,47.0
E,2334,210120000,19,L1,1C,18213952.6,95714965.773,763.651,43.0

```


```bash
± rnxnav_csv -h
usage: rnxnav_csv [-h] [-V] [-v] --nav_fn NAV_FN [--gnss GNSS]

argument_parser.py Convert RINEX navigation file to CSV file similar to those created by rtcm3_parser.py

options:
  -h, --help       show this help message and exit
  -V, --version    show program's version number and exit
  -v, --verbose    verbose level... repeat up to three times.
  --nav_fn NAV_FN  RINEX navigation filename
  --gnss GNSS      GNSS systems to convert (default: GE, select between G, R, E, C)
```

generates outputs converting each type of navigation message to a CSV file.
```text
Created for Beidou-D1: /home/amuls/cylab/TESTDATA/data2test/data/BRUX00BEL0_GREC_Beidou_D1.csv
Created for Beidou-D2: /home/amuls/cylab/TESTDATA/data2test/data/BRUX00BEL0_GREC_Beidou_D2.csv
Created for Galileo-FNAV: /home/amuls/cylab/TESTDATA/data2test/data/BRUX00BEL0_GREC_Galileo_FNAV.csv
Created for Galileo-INAV: /home/amuls/cylab/TESTDATA/data2test/data/BRUX00BEL0_GREC_Galileo_INAV.csv
Created for GPS-LNAV: /home/amuls/cylab/TESTDATA/data2test/data/BRUX00BEL0_GREC_GPS_LNAV.csv
Created for Glonass-FDMA: /home/amuls/cylab/TESTDATA/data2test/data/BRUX00BEL0_GREC_Glonass_FDMA.csv
```

```bash
rnx_csv -h
usage: rnx_csv [-h] [-V] [-v] --obs_fn OBS_FN --nav_fn NAV_FN [--gnss GNSS]

argument_parser.py Convert RINEX Obs & Nav file to CSV file similar to those created by rtcm3_parser.py

options:
  -h, --help       show this help message and exit
  -V, --version    show program's version number and exit
  -v, --verbose    verbose level... repeat up to three times.
  --obs_fn OBS_FN  RINEX observation filename
  --nav_fn NAV_FN  RINEX navigation filename
  --gnss GNSS      GNSS systems to convert (default: GE, select between G, R, E, C)
```