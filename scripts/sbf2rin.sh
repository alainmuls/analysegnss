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

# Add this section at the beginning of the script, right after the shebang
if [ $# -eq 0 ]; then
    usage
fi

if [ $? -ne 0 ]; then
  echo "getopt error"
  exit 2
fi

eval set -- $OPTIONS

# set the default options
RNX_DIR="."
EXCL_GNSS="RSCJI"

while true; do
  case "$1" in
    -h|--help)        usage; ;;
    -f|--file)        SBF_FN="$2" ; shift ;;
    -r|--rnx_dir)     RNX_DIR="$2" ; shift ;;
    -x|--excl_GNSS)   EXCL_GNSS="$2" ; shift ;;
    --)        shift ; break ;;
    *)         echo "unknown option: $1" ; exit 1 ;;
  esac
  shift
done

if [ $# -ne 0 ]; then
  echo "unknown option(s): $@"
  exit 1
fi

# locate sbf2rin and gfzrnx executables
SBF2RIN=`which sbf2rin`

# create the RNX_DIR if it does not exist
if [ ! -d ${RNX_DIR} ]; then
    mkdir -p ${RNX_DIR}
fi

OBS_OPTS=" -x "${EXCL_GNSS}" -s -D -v -R3 -l -O BEL -c"
NAV_OPTS=" -x "${EXCL_GNSS}" -v -R3 -l -O BEL -n P"

# switch to the RINEX directory
cd ${RNX_DIR}

echo -e "\e[1;34mCreating RINEX observation file in \e[1;32m${RNX_DIR}\e[0m"
${SBF2RIN} ${OBS_OPTS} -f ${SBF_FN} 
# fi

echo -e "\e[1;34mCreating RINEX navigation file in \e[1;32m${RNX_DIR}\e[0m"
${SBF2RIN} ${NAV_OPTS} -f ${SBF_FN}
