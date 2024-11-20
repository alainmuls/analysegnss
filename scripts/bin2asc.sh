#!/bin/bash 


OPTIONS=$(getopt -o hf:r:x: -l help,sbf_fn,rnx_dir,excl_GNSS -- "$@")

function usage {
    echo "$0 converts a SBF file to RINEX v3.x format"
    echo
    echo "usage: $0 [-h] -f SBF_fn [-r rnx_dir] [-x excl_GNSS]"
    echo "  -h              display help"
    echo "  -f SBF_fn       input SBF file"
    echo "  -r rnx_dir      directory for RINEX output (default .)"
    echo "  -x excl_GNSS    exclude GNSS (default: RSCJI)"
    exit 1
}


# create options for bin2asc
cmd_bin2asc = [
    run_bin2asc,
    "-f",
    self.sbf_fn,
    "-n",
    "NaN",
    "-E",
    "-r",
    "-t",
]
# "-b",
# self.epoch_start.strftime("%H:%M:%S"),
# "-e",
# self.epoch_end.strftime("%H:%M:%S"),
# add logging level to cmd_bin2asc when self._console_loglevel is DEBUG
if self._console_loglevel == logging.DEBUG:
    cmd_bin2asc.append("-v")
or sbf_block in lst_sbfblocks:
    cmd_bin2asc.append("-m")
    cmd_bin2asc.append(sbf_block)
