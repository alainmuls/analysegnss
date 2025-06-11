import csv
import logging

from pyubx2.ubxmessage import UBXMessage  # Import UBXMessage for type hinting

from analysegnss.utils.utilities import str_yellow, str_red
from analysegnss.ublox.ubx_definitions import (
    convert_ublox_gnss_identifier,
    get_ublox_signal_details,
)


class UBX_RXM_RAWX:
    """Class to manage the decoding of uBlox RXM-RAWX (0xB5 0x62) messages
    and writing of the data to a CSV file
    """

    def __init__(self, fn_rawx: str = "/tmp/ubx_rxm_rawx.csv") -> None:
        """
        Initialize instance of UBX_RXM_RAWX

        Args:
            fn_rawx (str): Path to the CSV file where RXM-RAWX data will be written.
        """

        # # init the global variables
        # config.initialize()

        self.logger = logging.getLogger("ubx_parser")

        # write the header line to the UBX_RXM_RAWX csv file
        self.fn_rawx = fn_rawx
        self.fd_rawx = open(self.fn_rawx, "w")
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

        self.logger.info(f"{str_yellow('UBX_RXM_RAWX')} initialized")

    def init_csv_header(self):
        """initializes the csv header for UBX message rxm_rawx"""

        # write the header line to the UBX_RXM_RAWX csv file
        self.writer.writerow(self.dict_obs.keys())
        self.fd_rawx.flush()

    def decode_rawx(self, rawx: UBXMessage) -> None:
        """decodes the RXM-RAWX message and writes the data to the csv file

        Args:
            rawx (UBXMessage): RXM-RAWX parsed UBXMessage object
        """
        essential_attrs = ["rcvTow", "week", "numMeas", "leapS"]
        missing_attrs = [attr for attr in essential_attrs if not hasattr(rawx, attr)]

        if missing_attrs:
            if self.logger:
                self.logger.error(
                    f"RXM-RAWX message is missing essential attribute(s): "
                    f"{str_red(', '.join(missing_attrs))}. Cannot process."
                )
            return

        rcvTow = getattr(rawx, "rcvTow", None)
        week = getattr(rawx, "week", None)
        numMeas = getattr(rawx, "numMeas", None)
        leapS = getattr(rawx, "leapS", None)
        # rprint(f"rcvTow: {rcvTow}, week: {week}, numMeas: {numMeas}, leapS: {leapS}")

        # clear content of dictionary for storing observables
        for k in self.dict_obs.keys():
            self.dict_obs[k].clear()

        # Iterate through the individual measurements.
        # pyubx2 stores these in a list of namedtuples (or similar objects)
        # in an attribute named after the group definition, which is 'group_R001' for RXM-RAWX.
        measurements_found_and_processed = False

        if numMeas is not None and numMeas > 0:
            # decode the RXM-RAWX message common elements

            if (
                hasattr(rawx, "group_R001")
                and getattr(rawx, "group_R001", None) is not None
            ):
                group = getattr(rawx, "group_R001")
                if isinstance(group, (list, tuple)) and len(group) == numMeas:
                    if self.logger:
                        self.logger.debug(
                            f"RXM-RAWX: Processing {numMeas} measurements via group_R001."
                        )
                    for meas_data in group:
                        # meas_data is an object/namedtuple with attributes like:
                        # prMes, cpMes, doMes, gnssId, svId, sigId, freqId, locktime, cno, trkStat
                        self.dict_obs["GNSS"].append(
                            convert_ublox_gnss_identifier(
                                gnss_id=meas_data.gnssId, logger=self.logger  # type: ignore
                            )
                        )
                        self.dict_obs["WKNR"].append(week)
                        self.dict_obs["TOW"].append(rcvTow)
                        self.dict_obs["PRN"].append(meas_data.svId)
                        # get UBX sigtype value and convert to frequency and signal type
                        sig_id_val = getattr(meas_data, "sigId", None)
                        freq_band, signal_code = get_ublox_signal_details(
                            gnss_id_num=meas_data.gnssId, sig_id=sig_id_val, logger=self.logger  # type: ignore
                        )  # sigId can be optional
                        self.dict_obs["cfreq"].append(freq_band)
                        self.dict_obs["sigt"].append(signal_code)

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
                            f"RXM-RAWX: 'group_R001' found, but its length ({len(group) if isinstance(group, (list, tuple)) else 'N/A'}) "
                            f"does not match numMeas ({numMeas}). Will attempt fallback."
                        )
            # else:  # hasattr(rawx, "group_R001") is False
            #     if self.logger:
            #         self.logger.warning(
            #             f"RXM-RAWX: 'group_R001' attribute NOT found for numMeas = {rawx.numMeas}. "
            #             "Will attempt fallback to suffixed attributes (e.g., svId_01)."
            #         )

            # Fallback to suffixed attributes if group_R001 processing was not successful or not possible
            if (
                not measurements_found_and_processed
                and numMeas is not None
                and numMeas > 0
            ):
                # if self.logger:
                #     self.logger.info(
                #         "RXM-RAWX: Attempting to process measurements using suffixed attributes."
                #     )
                processed_in_fallback = 0
                for i in range(numMeas):
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
                        self.dict_obs["GNSS"].append(
                            convert_ublox_gnss_identifier(
                                gnss_id=gnssId_val, logger=self.logger  # type: ignore
                            )
                        )
                        self.dict_obs["WKNR"].append(week)
                        self.dict_obs["TOW"].append(rcvTow)
                        self.dict_obs["PRN"].append(svId_val)

                        # get UBX sigtype value and convert to frequency and signal type
                        freq_band, signal_code = get_ublox_signal_details(
                            gnss_id_num=gnssId_val, sig_id=sigId_val, logger=self.logger  # type: ignore
                        )  # sigId can be optional
                        self.dict_obs["cfreq"].append(freq_band)
                        self.dict_obs["sigt"].append(signal_code)

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
                        f"RXM-RAWX: Fallback to suffixed attributes for {numMeas} measurements "
                        "did not yield any complete measurements."
                    )

        if not measurements_found_and_processed and numMeas is not None and numMeas > 0:
            if self.logger:
                self.logger.error(
                    f"RXM-RAWX: Failed to process any of the {numMeas} measurements for TOW {rcvTow}. "
                    "Check message integrity and pyubx2 compatibility."
                )
        elif numMeas == 0 and self.logger:  # This is a normal case
            self.logger.debug(
                f"RXM-RAWX: numMeas is 0 for TOW {rcvTow}, no measurements to process."
            )

        # After attempting to collect all measurements for this message (if any), write them to the CSV.
        # This will write an empty set of rows if dict_obs lists are empty (e.g., if numMeas was 0 or processing failed).
        rows_to_write = zip(*self.dict_obs.values())
        self.writer.writerows(rows_to_write)
        self.fd_rawx.flush()

    def close(self) -> None:
        """Closes the CSV file."""
        if self.fd_rawx and not self.fd_rawx.closed:
            self.fd_rawx.close()
            self.logger.info(f"UBX_RXM_RAWX CSV file '{self.fn_rawx}' closed.")

    def __del__(self) -> None:
        """Ensures the file is closed when the object is garbage collected.
        Avoids logging as the logging module may not be available during
        interpreter shutdown.
        """
        try:
            if hasattr(self, "fd_rawx") and self.fd_rawx and not self.fd_rawx.closed:
                self.fd_rawx.close()
        except Exception:
            # It's generally good practice to suppress exceptions in __del__
            pass
