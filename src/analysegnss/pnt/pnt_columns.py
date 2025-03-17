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
}


def get_pnt_columns(source: str) -> PNTColumns:
    """Get the correct column names for the given source"""
    return COLUMN_MAPPINGS[source]


def get_column_mapping_source_to_csv(
    source: str, include_sd: bool = True
) -> Dict[str, Dict[str, pl.DataType]]:
    """get a mapping of PNT source columns to standard PNT_CSV columns (which is the default output format of csv files)

    Args:
        source: Source type (RTK, PPK, GLABNG, NMEA, PNT_CSV)
        include_sd: Whether to include standard deviation columns

    Returns:
        column_mapping_source_to_csv (dict): mapping of source columns to standard columns
    """
    source_pnt_cols = get_pnt_columns(source)
    standard_pnt_cols = get_pnt_columns("PNT_CSV")

    column_mapping_source_to_csv = {
        source_pnt_cols.east: dict(column_name=standard_pnt_cols.east, dtype=pl.Float64),
        source_pnt_cols.north: dict(column_name=standard_pnt_cols.north, dtype=pl.Float64),
        source_pnt_cols.height: dict(column_name=standard_pnt_cols.height, dtype=pl.Float64),
        source_pnt_cols.time: dict(column_name=standard_pnt_cols.time, dtype=pl.Datetime),
        source_pnt_cols.quality_mapping.quality_column: dict(
            column_name=standard_pnt_cols.quality_mapping.quality_column,
            dtype=pl.Utf8,
        ),
        source_pnt_cols.nrSVN: dict(column_name=standard_pnt_cols.nrSVN, dtype=pl.UInt8),
    }

    if include_sd:
        column_mapping_source_to_csv.update(
            {
                source_pnt_cols.sdn: dict(column_name=standard_pnt_cols.sdn, dtype=pl.Float64),
                source_pnt_cols.sde: dict(column_name=standard_pnt_cols.sde, dtype=pl.Float64),
                source_pnt_cols.sdu: dict(column_name=standard_pnt_cols.sdu, dtype=pl.Float64),
            }
        )

    return column_mapping_source_to_csv


def get_required_columns_from_pnt_source(
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
