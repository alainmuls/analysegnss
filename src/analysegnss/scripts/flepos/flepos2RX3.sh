#!/bin/bash
# Script to convert FLEPOS data to RX3 format

# Add proper error handling
set -e  # Exit on error

OPTIONS=$(getopt -o hvs:d:r: -l help,verbose,station,doy,rnx3_dir -- "$@")

function usage {
    echo "$0 converts FLEPOS RINEX v2 files to RINEX v3.x format"
    echo
    echo "usage: $0 [-h] -f SBF_fn [-r rnx_dir] [-x excl_GNSS]"
    echo "  -h              display help"
    echo "  -s station      FLEPOS station name"
    echo "  -d DOY          day of year"
    echo "  -r rnx3_dir     directory for RINEX v3.x output (default .)"
    echo "  -v              verbose output"
    exit 1
}


# Add this section at the beginning of the script, right after the shebang
if [ $# -eq 0 ]; then
    usage
fi

if [ $? -ne 0 ]; then
  echo "getopt error"
  exit 2
fi

eval set -- "${OPTIONS}"


gfzrnx -finp `ls -1 BERT3610.24[lngc]` -fout ::RX3::00,BEL -f
gfzrnx -finp BERT3610.24o -fout ::RX3::00,BEL