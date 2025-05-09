import csv
import logging

from rich import print as rprint

from analysegnss.utils.utilities import str_yellow
from pyubx2.ubxmessage import UBXMessage  # Import UBXMessage for type hinting


class UBX_RAWX:
    """manages the decoding of uBlox RXM-RAWX (0xB5 0x62) messages
    and writing of the data to a CSV file
    """

    def __init__(self, fn_rawx: str = "/tmp/ubx_rawx.csv") -> None:
        """initializes instance of UBX_RAWX"""

        # # init the global variables
        # config.initialize()

        self.logger = logging.getLogger("ubx_parser")

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

    def decode_rawx(self, rawx: UBXMessage) -> None:
        """decodes the RXM-RAWX message and writes the data to the csv file
        Args:
            rawx (UBXMessage): RXM-RAWX parsed UBXMessage object
        """
        rprint(rawx.identity)

        # clear content of dictionary for storing observables
        for k in self.dict_obs.keys():
            self.dict_obs[k].clear()

        # decode the RXM-RAWX message common elements
        rcvTow = rawx.rcvTow
        week = rawx.week
        numMeas = rawx.numMeas
        leapS = rawx.leapS
        rprint(f"rcvTow: {rcvTow}, week: {week}, numMeas: {numMeas}, leapS: {leapS}")

        # Iterate through the individual measurements.
        # pyubx2 stores these in a list of namedtuples (or similar objects)
        # in an attribute named after the group definition, which is 'group_R001' for RXM-RAWX.
        measurements_found_and_processed = False
        if rawx.numMeas > 0:
            if hasattr(rawx, "group_R001"):
                # Preferred method: iterate through the group
                if len(rawx.group_R001) == rawx.numMeas:
                    if self.logger:
                        self.logger.debug(
                            f"RXM-RAWX: Processing {rawx.numMeas} measurements via group_R001."
                        )
                    for meas_data in rawx.group_R001:
                        # meas_data is an object/namedtuple with attributes like:
                        # prMes, cpMes, doMes, gnssId, svId, sigId, freqId, locktime, cno, trkStat
                        self.dict_obs["GNSS"].append(meas_data.gnssId)
                        self.dict_obs["WKNR"].append(week)
                        self.dict_obs["TOW"].append(rcvTow)
                        self.dict_obs["PRN"].append(meas_data.svId)
                        self.dict_obs["cfreq"].append(meas_data.freqId)
                        self.dict_obs["sigt"].append(
                            getattr(meas_data, "sigId", None)
                        )  # sigId can be optional
                        self.dict_obs["C"].append(meas_data.prMes)
                        self.dict_obs["L"].append(meas_data.cpMes)
                        self.dict_obs["D"].append(meas_data.doMes)
                        self.dict_obs["S"].append(meas_data.cno)
                        self.dict_obs["locktime"].append(meas_data.locktime)

                        # 'halfcycleamb' from your dict_obs.
                        # Bit 2 of trkStat: "Carrier phase half-cycle ambiguity reported" (0=no, 1=yes)
                        half_cycle_ambiguity_reported = (meas_data.trkStat & 0x04) >> 2
                        self.dict_obs["halfcycleamb"].append(
                            half_cycle_ambiguity_reported
                        )
                    measurements_found_and_processed = True
                else:  # group_R001 exists, but length mismatch
                    if self.logger:
                        self.logger.warning(
                            f"RXM-RAWX: 'group_R001' found, but its length ({len(rawx.group_R001)}) "
                            f"does not match numMeas ({rawx.numMeas}). Will attempt fallback."
                        )
            else:  # hasattr(rawx, "group_R001") is False
                if self.logger:
                    self.logger.warning(
                        f"RXM-RAWX: 'group_R001' attribute NOT found for numMeas = {rawx.numMeas}. "
                        "Will attempt fallback to suffixed attributes (e.g., svId_01)."
                    )

            # Fallback to suffixed attributes if group_R001 processing was not successful or not possible
            if not measurements_found_and_processed and rawx.numMeas > 0:
                if self.logger:
                    self.logger.info(
                        "RXM-RAWX: Attempting to process measurements using suffixed attributes."
                    )
                processed_in_fallback = 0
                for i in range(rawx.numMeas):
                    idx_str = f"_{i+1:02d}"  # e.g., _01, _02, ...
                    try:
                        # Attempt to get all attributes for this measurement index
                        # If any are missing, AttributeError will be raised, and we'll skip this measurement.
                        gnssId_val = getattr(rawx, f"gnssId{idx_str}")
                        svId_val = getattr(rawx, f"svId{idx_str}")
                        prMes_val = getattr(rawx, f"prMes{idx_str}")
                        cpMes_val = getattr(rawx, f"cpMes{idx_str}")
                        doMes_val = getattr(rawx, f"doMes{idx_str}")
                        freqId_val = getattr(rawx, f"freqId{idx_str}")
                        # sigId might not exist in older message versions or if message is truncated.
                        # Default to None if not found, rather than erroring out immediately for this field.
                        sigId_val = getattr(rawx, f"sigId{idx_str}", None)
                        cno_val = getattr(rawx, f"cno{idx_str}")
                        locktime_val = getattr(rawx, f"locktime{idx_str}")
                        halfCyc_val = getattr(rawx, f"halfCyc{idx_str}")

                        # All essential attributes for this measurement index found, now append
                        self.dict_obs["GNSS"].append(gnssId_val)
                        self.dict_obs["WKNR"].append(week)
                        self.dict_obs["TOW"].append(rcvTow)
                        self.dict_obs["PRN"].append(svId_val)
                        self.dict_obs["cfreq"].append(freqId_val)
                        self.dict_obs["sigt"].append(sigId_val)
                        self.dict_obs["C"].append(prMes_val)
                        self.dict_obs["L"].append(cpMes_val)
                        self.dict_obs["D"].append(doMes_val)
                        self.dict_obs["S"].append(cno_val)
                        self.dict_obs["locktime"].append(locktime_val)
                        self.dict_obs["halfcycleamb"].append(halfCyc_val)
                        processed_in_fallback += 1

                    except AttributeError as e:
                        if self.logger:
                            self.logger.error(
                                f"RXM-RAWX: Fallback failed for measurement index {i} "
                                f"due to missing attribute: {e}. Skipping this measurement."
                            )
                        # If any essential attribute is missing for this index, we skip this measurement entirely
                        # to avoid partial records in dict_obs for this specific measurement.
                        continue

                if processed_in_fallback > 0:
                    measurements_found_and_processed = True
                elif (
                    self.logger
                ):  # Fallback attempted but processed nothing, though numMeas > 0
                    self.logger.warning(
                        f"RXM-RAWX: Fallback to suffixed attributes for {rawx.numMeas} measurements "
                        "did not yield any complete measurements."
                    )

        if not measurements_found_and_processed and rawx.numMeas > 0:
            if self.logger:
                self.logger.error(
                    f"RXM-RAWX: Failed to process any of the {rawx.numMeas} measurements for TOW {rcvTow}. "
                    "Check message integrity and pyubx2 compatibility."
                )
        elif rawx.numMeas == 0 and self.logger:  # This is a normal case
            self.logger.debug(
                f"RXM-RAWX: numMeas is 0 for TOW {rcvTow}, no measurements to process."
            )

        # After attempting to collect all measurements for this message (if any), write them to the CSV.
        # This will write an empty set of rows if dict_obs lists are empty (e.g., if numMeas was 0 or processing failed).
        rows_to_write = zip(*self.dict_obs.values())
        self.writer.writerows(rows_to_write)
        self.fd_rawx.flush()
