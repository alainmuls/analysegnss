# Third-party imports
import polars as pl
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

# Local application imports
from analysegnss.gnss.general_pnt_quality_dict import GENERAL_PNT_QUALITY_ID


@dataclass
class PNTQualityMapping:
    quality_column: str
    quality_dict: Dict


@dataclass
class PNTColumns:
    east: str
    north: str
    height: str
    time: str
    quality_mapping: PNTQualityMapping
    sde: str
    sdn: str
    sdu: str
    nrSVN: str


# Define mappings for different sources
COLUMN_MAPPINGS: Dict[str, PNTColumns] = {
    "RTK": PNTColumns(
        east="UTM.E",
        north="UTM.N",
        height="orthoH",
        time="DT",
        quality_mapping=PNTQualityMapping("pnt_qual", GENERAL_PNT_QUALITY_ID),
        sde="SD_lon [m]",
        sdn="SD_lat [m]",
        sdu="SD_hgt [m]",
        nrSVN="NrSV",
    ),
    "PPK": PNTColumns(
        east="UTM.E",
        north="UTM.N",
        height="orthoH",
        time="DT",
        quality_mapping=PNTQualityMapping("pnt_qual", GENERAL_PNT_QUALITY_ID),
        sde="sde(m)",
        sdn="sdn(m)",
        sdu="sdu(m)",
        nrSVN="ns",
    ),
    "GLABNG": PNTColumns(
        east="UTM.E",
        north="UTM.N",
        height="orthoH",
        time="DT",
        quality_mapping=PNTQualityMapping("pnt_qual", GENERAL_PNT_QUALITY_ID),
        sde="sd.E",
        sdn="sd.N",
        sdu="sd.U",
        nrSVN="#SVs",
    ),
    "NMEA": PNTColumns(
        east="UTM.E",
        north="UTM.N",
        height="orthoH",
        time="DT",
        quality_mapping=PNTQualityMapping("pnt_qual", GENERAL_PNT_QUALITY_ID),
        sde="sdlon(m)",  # TODO convert sdlon to sdE (if region is small: (BETER= (nautical mile (=1852m) * 60 * 360) vor omtrek aarde: omtrek_aarde/360)*sdlon = sde). Or use PROJ lib
        sdn="sdlat(m)",
        sdu="sdH(m)",
        nrSVN="num_sats",
    ),
    "PNT_CSV": PNTColumns(
        east="UTM.E",
        north="UTM.N",
        height="orthoH",
        time="DT",
        quality_mapping=PNTQualityMapping("pnt_qual", GENERAL_PNT_QUALITY_ID),
        sde="sde(m)",
        sdn="sdn(m)",
        sdu="sdu(m)",
        nrSVN="num_sats",
    ),
    # "GLABNG": UTMColumns(
    #     east="delta.E",
    #     north="delta.N",
    #     height="delta.U",
    #     time="DT",
    #     quality_mapping=UTMQualityMapping("mode", glabc.DICT_PROCESSING_MODE),
    #     sde="sd.E",
    #     sdn="sd.N",
    #     sdu="sd.U",
    #     nrSVN="#SVs",
    # ),
    "STANDARD_PNT_FORMAT": PNTColumns(
        east="UTM.E",
        north="UTM.N",
        height="orthoH",
        time="DT",
        quality_mapping=PNTQualityMapping("pnt_qual", GENERAL_PNT_QUALITY_ID),
        sde="sde(m)",
        sdn="sdn(m)",
        sdu="sdu(m)",
        nrSVN="num_sats",
    ),
}

COLUMN_DTYPE_MAPPINGS: Dict[pl.DataType, List[str]] = {
    pl.Float64: [
        "UTM.E",
        "UTM.N",
        "orthoH",
        "sde(m)",
        "sdn(m)",
        "sdu(m)",
        "SD_lon [m]",
        "SD_lat [m]",
        "SD_hgt [m]",
        "sd.E",
        "sd.N",
        "sd.U",
        "sdlon(m)",
        "sdlat(m)",
        "sdH(m)",
        "delta.E",
        "delta.N",
        "delta.U",
    ],
    pl.UInt8: ["num_sats", "NrSV", "ns", "#SVs"],
    pl.Datetime: ["DT"],
    pl.Utf8: ["pnt_qual", "source", "mode"],
}


def get_pnt_columns(source: str) -> PNTColumns:
    """Get the correct column names for the given source"""
    return COLUMN_MAPPINGS[source]


def column_mapping_source_to_standard(
    source: str, include_sd: bool = True
) -> Dict[str, str]:
    """get a mapping of PNT source columns to standard PNT_FORMAT columns (which is the default output format of csv files)

    Args:
        source: Source type (RTK, PPK, GLABNG, NMEA, PNT_CSV)
        include_sd: Whether to include standard deviation columns

    Returns:
        column_mapping_source_to_standard (dict): mapping of source columns to standard columns
    """
    source_pnt_cols = get_pnt_columns(source)
    standard_pnt_cols = get_pnt_columns("STANDARD_PNT_FORMAT")

    column_mapping_source_to_standard = {
        source_pnt_cols.east: standard_pnt_cols.east,
        source_pnt_cols.north: standard_pnt_cols.north,
        source_pnt_cols.height: standard_pnt_cols.height,
        source_pnt_cols.time: standard_pnt_cols.time,
        source_pnt_cols.quality_mapping.quality_column: standard_pnt_cols.quality_mapping.quality_column,
        source_pnt_cols.nrSVN: standard_pnt_cols.nrSVN,
    }

    if include_sd:
        column_mapping_source_to_standard.update(
            {
                source_pnt_cols.sdn: standard_pnt_cols.sdn,
                source_pnt_cols.sde: standard_pnt_cols.sde,
                source_pnt_cols.sdu: standard_pnt_cols.sdu,
            }
        )

    return column_mapping_source_to_standard


def get_required_columns_for_pnt_source(
    source: str, include_sd: bool = True
) -> List[str]:
    """Get the list of required columns for a source

    Args:
        source: Source type (RTK, PPK, GLABNG, NMEA, PNT_CSV)
        include_sd: Whether to include standard deviation columns

    Returns:
        required_pnt_cols (list): List of required column names for the source
    """
    source_pnt_cols = get_pnt_columns(source)

    required_pnt_cols = [
        source_pnt_cols.east,
        source_pnt_cols.north,
        source_pnt_cols.height,
        source_pnt_cols.time,
        source_pnt_cols.quality_mapping.quality_column,
        source_pnt_cols.nrSVN,
    ]

    if include_sd:
        required_pnt_cols.extend(
            [
                source_pnt_cols.sdn,
                source_pnt_cols.sde,
                source_pnt_cols.sdu,
            ]
        )

    return required_pnt_cols


def get_column_dtypes(
    columns_to_cast: List[str],
) -> Tuple[Dict[str, pl.DataType], List[str]]:
    """Get the mapping of column names to their data types

    Args:
        columns_to_cast (list): List of column names or Polars expressions to determine data types for

    Returns:
        Tuple:
        - column_dtype (dict): Dict mapping column names to Polars dtypes
        - failed_casting_columns (list): List of column names that are not in COLUMN_DTYPE_MAPPINGS
    """
    column_dtype = {}

    # Extract column names. When using alias() to rename pl.columns,
    # the col names become Polars expressions. Then use meta.output_name() to get the column name
    column_names = []
    for col in columns_to_cast:
        if isinstance(col, pl.Expr):
            column_names.append(col.meta.output_name())
        elif isinstance(col, str):
            column_names.append(col)
        else:
            column_names.append(str(col))

    # Get dtype mapping
    for dtype, columns in COLUMN_DTYPE_MAPPINGS.items():
        for col_name in column_names:
            if col_name in columns:
                column_dtype[col_name] = dtype

    # Checking for columns that are not in COLUMN_DTYPE_MAPPINGS
    failed_casting_columns = [col for col in column_names if col not in column_dtype]

    return column_dtype, failed_casting_columns
