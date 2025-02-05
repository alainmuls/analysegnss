from dataclasses import dataclass
from typing import Callable, Dict

from analysegnss.nmea import nmea_constants as nmeac
from analysegnss.rtkpos import rtk_constants as rtkc
from analysegnss.sbf import sbf_constants as sbfc
from analysegnss.glabng import glab_constants as glabc


@dataclass
class UTMQualityMapping:
    columns: str
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


# Define mappings for different origins
COLUMN_MAPPINGS: Dict[str, UTMColumns] = {
    "RTK": UTMColumns(
        east="UTM.E",
        north="UTM.N",
        height="orthoH",
        time="DT",
        quality_mapping=UTMQualityMapping("Type", sbfc.DICT_SBF_PVTMODE),
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
        quality_mapping=UTMQualityMapping("Q", rtkc.DICT_RTK_PVTMODE),
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
        quality_mapping=UTMQualityMapping("pvt_qual", nmeac.DICT_NMEA_PVT_QUALITY),
        #sde="sdlon(m)", #TODO convert sdlon to sdE (if region is small: (omtrek_aarde/360)*sdlon = sde). Or use PROJ lib
        #sdn="sdlat(m)",
        sdu="sdH(m)",
        nrSVN="num_sats",
    ),
    # TODO problem is that pvt_qual dict differs between all solution types. A fix could be to use a general pvt_qual dict for all.
    # This can be achieved by mapping the pvt_qual values to a general pvt_qual  dict in
    "PNT_CSV": UTMColumns(
        east="UTM.E",
        north="UTM.N",
        height="orthoH",
        time="DT",
        quality_mapping=UTMQualityMapping("mode", nmeac.DICT_NMEA_PVT_QUALITY),
        #sde="sdlon(m)",
        #sdn="sdlat(m)",
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


def get_utm_columns(origin: str) -> UTMColumns:
    """Get the correct column names for the given origin"""
    return COLUMN_MAPPINGS[origin]
