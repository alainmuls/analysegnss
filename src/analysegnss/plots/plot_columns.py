# Third-party imports
from dataclasses import dataclass
from typing import Dict

# Local application imports
from analysegnss.gnss.general_pvt_quality_dict import GENERAL_PVT_QUALITY_ID
from analysegnss.nmea import nmea_constants as nmeac
from analysegnss.rtkpos import rtklib_constants as rtklibc
from analysegnss.sbf import sbf_constants as sbfc
from analysegnss.glabng import glab_constants as glabc


@dataclass
class UTMQualityMapping:
    quality_column: str
    quality_dict: Dict


@dataclass
class UTMColumns:
    east: str
    north: str
    height: str
    time: str
    quality_mapping: UTMQualityMapping
    sde: str
    sdn: str
    sdu: str
    nrSVN: str


# Define mappings for different sources
COLUMN_MAPPINGS: Dict[str, UTMColumns] = {
    "RTK": UTMColumns(
        east="UTM.E",
        north="UTM.N",
        height="orthoH",
        time="DT",
        quality_mapping=UTMQualityMapping("pvt_qual", GENERAL_PVT_QUALITY_ID),
        sde="SD_lon [m]",
        sdn="SD_lat [m]",
        sdu="SD_hgt [m]",
        nrSVN="NrSV",
    ),
    "PPK": UTMColumns(
        east="UTM.E",
        north="UTM.N",
        height="orthoH",
        time="DT",
        quality_mapping=UTMQualityMapping("pvt_qual", GENERAL_PVT_QUALITY_ID),
        sde="sde(m)",
        sdn="sdn(m)",
        sdu="sdu(m)",
        nrSVN="ns",
    ),
    "GLABNG": UTMColumns(
        east="UTM.E",
        north="UTM.N",
        height="orthoH",
        time="DT",
        quality_mapping=UTMQualityMapping("mode", glabc.DICT_PROCESSING_MODE),
        sde="sd.E",
        sdn="sd.N",
        sdu="sd.U",
        nrSVN="#SVs",
    ),
    "NMEA": UTMColumns(
        east="UTM.E",
        north="UTM.N",
        height="orthoH",
        time="DT",
        quality_mapping=UTMQualityMapping("pvt_qual", GENERAL_PVT_QUALITY_ID),
        sde="sdlon(m)",  # TODO convert sdlon to sdE (if region is small: (BETER= (nautical mile (=1852m) * 60 * 360) vor omtrek aarde: omtrek_aarde/360)*sdlon = sde). Or use PROJ lib
        sdn="sdlat(m)",
        sdu="sdH(m)",
        nrSVN="num_sats",
    ),
    "PNT_CSV": UTMColumns(
        east="UTM.E",
        north="UTM.N",
        height="orthoH",
        time="DT",
        quality_mapping=UTMQualityMapping("pvt_qual", GENERAL_PVT_QUALITY_ID),
        sde="sdlon(m)",
        sdn="sdlat(m)",
        sdu="sdH",
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


def get_utm_columns(source: str) -> UTMColumns:
    """Get the correct column names for the given source"""
    return COLUMN_MAPPINGS[source]
