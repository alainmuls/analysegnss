from dataclasses import dataclass
from typing import Callable, Dict

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
