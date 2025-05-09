import csv
import logging

from analysegnss.utils.utilities import str_yellow


class UBX_RAWX:
    """manages the decoding of uBlox RXM-RAWX (0xB5 0x62) messages
    and writing of the data to a CSV file
    """

    def __init__(self, fn_rawx: str = "/tmp/ubx_rawx.csv") -> None:
        """initializes instance of UBX_RAWX"""

        # # init the global variables
        # config.initialize()

        self.logger = logging.getLogger("ubx_parser")

        # # keep the week number
        # self.WKNR = None
        # self.gnss = None
        # self.TOW = None
        # self.NSats = None
        # self.NCells = None
        # self.ref_station = None
        # self.rough_data = []
        # self.sigmap = None  # links RINEX codes to frequency name
        # self.cfreq_khz = None  # frequency [kHz] of the signal

        # write the header line to the UBX_RAWX csv file
        self.fd_rawx = open(fn_rawx, "w")
        self.writer = csv.writer(self.fd_rawx, delimiter=",")

        # store the observables according to this dictionary
        self.dict_obs = {
            "GNSS": [],
            "WKNR": [],
            "TOW": [],
            "PRN": [],
            "cfreq": [],
            "sigt": [],
            "C": [],
            "L": [],
            "D": [],
            "S": [],
            "locktime": [],
            "halfcycleamb": [],
        }
        self.init_csv_header()

        self.logger.info(f"{str_yellow('UBX_RAWX')} initialized")

    def init_csv_header(self):
        """initializes the csv header for RTCM message rxm_rawx"""

        # write the header line to the UBX_RAWX csv file
        self.writer.writerow(self.dict_obs.keys())
        self.fd_rawx.flush()
