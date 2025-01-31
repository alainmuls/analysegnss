
## SBF related classes and functions

### Class `SBF`

The `sbf_class` is a class that reads and parses SBF files. The class  has the following fields:
- `sbf_fn`: the SBF filename, mandatory
- `start_time`: the start time of the SBF file, optional
- `end_time`: the end time of the SBF file, optional
- `logger`: the logger object, optional

During initialization of the class, the fields are validated.

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
    - `"Height [m]", "Undulation [m]"` are combined to `"orthoH [m]"`.

- `def used_columns(self, sbf_block: str) -> list:`
    The `bin2asc` conversion creates CSV files with a lot of information which are not all needed. This method selects the columns used for the subsequent analysis or processing. The columns are selected based on the SBF block name and the `dtype` of the column is set to the [polars](https://docs.pola.rs/) type definition, reducing the memory usage of the SBF block [polars dataframe](https://docs.pola.rs/).
        - _Remark: currently only implemented for the `PVTGeodetic2` SBF block._

- `def add_columns(self, block_df: pl.DataFrame) -> pl.DataFrame:`
    Some data are removed while columns are added to the dataframe by default based on the requested SBF block.
    - Data rows without valid PNT solution are excluded.
    - The columns `"SVID"` and `"PRN"` are converted to `"PRN"` and `"SVID"` respectively.
    - The columns `"Latitude [rad]", "Longitude [rad]"` are converted to `"Latitude [deg]"` and `"Longitude [deg]"` and to `"UTM.E", "UTM.N"` using the `utm` module. The geodetic coordinates in radians are subsequently dropped.
    - The columns `"Height [m]", "Undulation [m]"` are combined to `"orthoH [m]"`
    - The columns `"WNc [w]", "TOW [0.001 s]"` are converted to a Python `datetime` object.
    - If needed the SBF block containing the geodetic covariance matrix is transformed to standard deviations (only diagonal elements)?
    - 
In the `sbf` directory the file `sbf_constants.py` contains the constants used for interpreting some SBF data fields.


### Python script `rtk_pvtgeod` 

The script `rtk_pvtgeod` is a Python script that reads and parses the `PVTGeodetic2` SBF block from an SBF file, creates the CSV file and loads into a dataframe. The script has the following options:

```bash
± rtk_pvtgeod -h
usage: rtk_pvtgeod [-h] --sbf_fn SBF_FN [--sbf2asc] [--sd] [-V] [-v]

argument_parser.py analysis of SBF data

options:
  -h, --help       show this help message and exit
  --sbf_fn SBF_FN  input SBF filename
  --sbf2asc        Using sbf2asc instead of bin2asc as sbf converter.
  --sd             add standard deviation to the plot
  -V, --version    show program's version number and exit
  -v, --verbose    verbose level... repeat up to three times.

```

When the option `--sd` is used the standard deviation is added to the dataframe by parsing the `PosCovGeodetic1` SBF block and converting the diagonal covariance elements to standard deviations. The resulting dataframe has the following columns:
```
['TOW [0.001 s]', 'WNc [w]', 'Type', 'Error', 'Height [m]', 'Undulation [m]', 'COG [°]', 
'NrSV', 'MeanCorrAge [0.01 s]', 'SignalInfo', 'DT', 'latitude [deg]', 'longitude [deg]', 
'UTM.E', 'UTM.N', 'orthoH', 'TOW [0.001 s]_right', 'WNc [w]_right', 
'SD_lat [m]', 'SD_lon [m]', 'SD_hgt [m]']
```

The standard deviation columns are only available when the option `--sd` is used.



---

Return to  [top level readme](../../../README.md)