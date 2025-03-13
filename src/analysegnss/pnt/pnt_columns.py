# Third-party imports
from dataclasses import dataclass
from typing import Dict

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

# TODO ADD dtype schema

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
