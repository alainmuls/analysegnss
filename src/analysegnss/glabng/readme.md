
## GALBNG related classes and functions

The `GLABNG` class is used to read and parse sections of the gLABng files.  The class has the following fields:
- `glab_fn`: the GLABNG filename, mandatory
- `start_time`: the start time, optional
- `end_time`: the end time, optional
- `logger`: the logger object, optional

The class has the following methods:
- `def glab_dataframe(self, lst_sections: list[str] = ["OUTPUT"]) -> dict:`    
    This method parses specified sections from gLAB file and returns a dictionary of dataframes where the section name is the key and the dataframe is the value. 
- `def load_section_data(self, section: str, section_data: list[str]) -> pl.DataFrame:`
    This method parses a specific section and returns a polars dataframe. It combines the data columns `["Year", "DOY", "SOD"]`  into a single column `"DT"` in the format `"YYYY-MM-DD HH:MM:SS"`.

    When the section is `"OUTPUT"`, the method also adds the following columns:
    - `["UTM.E", "UTM.N"]"` by calling the `utm.latlon_to_utm` function.
    - `["undulation", "orthoH""]` by calling the `gh_model` function from `src/analysegnss/gnss/geoid.py` script.

### Python script `glab_parser`

The script `glab_parser` is used to parse the gLABng files and extract the data from specific sections. Currently only the `"OUTPUT"` and `SATSEL` sections are parsed. The script has the following options:

```bash
± glab_parser -h
usage: glab_parser [-h] [-V] [-v] --glab_fn GLAB_FN [--section SECTION]

argument_parser.py parses the gLAB file.

options:
  -h, --help         show this help message and exit
  -V, --version      show program's version number and exit
  -v, --verbose      verbose level... repeat up to three times.
  --glab_fn GLAB_FN  gLAB produced file
  --section SECTION  Comma-separated gLAB sections to parse (default: OUTPUT) 
                        (e.g. OUTPUT,SATSEL,INFO)
```

The dataframe obtained when parsing the `"OUTPUT"` section contains following columns:
```
['mode', 'dir', '#SVs', '#GNSSs', 'GNSSs', 'sdXYZ', 'lat', 'lon', 'ellH', 
'delta.N', 'delta.E', 'delta.U', 'sd.N', 'sd.E', 'sd.U', 
'GNSSclock', 'clk_off', 'clk_err', 
'GDOP', 'PDOP', 'TDOP', 'HDOP', 'VDOP', 
'ZTDinc', 'ZTDecl', 'sd.ZTD', 
'DT', 'UTM.E', 'UTM.N', 'undulation', 'orthoH']
```

The dataframe obtained when parsing the `"SATSEL"` section contains following columns:
```
['SATSEL', 'Year', 'DOY', 'SOD', 'DT', 'GNSS', 'PRN', 'code', 'code_desc']
```
