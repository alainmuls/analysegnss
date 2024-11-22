#!/bin/bash 


OPTIONS=$(getopt -o hvf:r:x:b:e: -l help,sbf_fn,rnx_dir,excl_GNSS,begin_epoch,end_epoch -- "$@")

function usage {
    echo "$0 converts a SBF file to RINEX v3.x format"
    echo
    echo "usage: $0 [-h] -f SBF_fn [-r rnx_dir] [-x excl_GNSS]"
    echo "  -h              display help"
    echo "  -f SBF_fn       input SBF file"
    echo "  -x excl_GNSS    exclude GNSS (default: RSCJI)"
    echo "  -b begin_epoch  begin epoch (default: None, format: YYYY-MM-DD_HH:MM:SS or HH:MM:SS)"
    echo "  -e end_epoch    end epoch (default: None, format: YYYY-MM-DD_HH:MM:SS or HH:MM:SS)"
    echo "  -r rnx_dir      directory for RINEX output (default .)"
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

eval set -- $OPTIONS

# set the default options
RNX_DIR="."
EXCL_GNSS="RSCJI"

while true; do
  case "$1" in
    -h|--help)          usage; ;;
    -f|--file)          SBF_FN="$2" ; shift ;;
    -x|--excl_GNSS)     EXCL_GNSS="$2" ; shift ;;
    -b|--begin_epoch)   BEGIN_EPOCH="$2" ; shift ;;
    -e|--end_epoch)     END_EPOCH="$2" ; shift ;;
    -r|--rnx_dir)       RNX_DIR="$2" ; shift ;;
    -v|--verbose)       VERBOSE=true ;;
    --)                 shift ; break ;;
    *)                  echo "unknown option: $1" ; exit 1 ;;
  esac
  shift
done

if [ $# -ne 0 ]; then
  echo "unknown option(s): $@"
  exit 2
fi

# locate sbf2rin executable
SBF2RIN=$(which sbf2rin)
if [ -z "${SBF2RIN}" ]; then
    echo -e "\e[1;31mError: sbf2rin executable not found in PATH\e[0m"
    exit 3
fi

# create the RNX_DIR if it does not exist
if [ ! -d ${RNX_DIR} ]; then
    mkdir -p ${RNX_DIR}
fi

opts_timing=""
# check for existence of BEGIN_TIME, if specified in correct format, than add to opts_timing
if [ -n "${BEGIN_EPOCH}" ]; then
    if [[ "${BEGIN_EPOCH}" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}:[0-9]{2}:[0-9]{2}$ ]]; then
        opts_timing="${opts_timing} -b ${BEGIN_EPOCH}"
    elif [[ "${BEGIN_EPOCH}" =~ ^[0-9]{2}:[0-9]{2}:[0-9]{2}$ ]]; then
        opts_timing="${opts_timing} -b ${BEGIN_EPOCH}"
    fi
fi
# check for existence of END_TIME, if specified in correct format, than add to opts_timing
if [ -n "${END_EPOCH}" ]; then
    if [[ "${END_EPOCH}" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}:[0-9]{2}:[0-9]{2}$ ]]; then
        opts_timing="${opts_timing} -e ${END_EPOCH}"
    elif [[ "${END_EPOCH}" =~ ^[0-9]{2}:[0-9]{2}:[0-9]{2}$ ]]; then
        opts_timing="${opts_timing} -e ${END_EPOCH}"
    fi
fi

# check if verbose mode was specified
if [ "${VERBOSE}" = true ]; then
    opts_timing="${opts_timing} -v"
fi


# create the OUT_DIR if it does not exist
SBF_DIR=$(dirname "${SBF_FN}")  # Get the directory of the input SBF file
RNX_DIR="${SBF_DIR}/${RNX_DIR}"  # Combine paths to get absolute output directory
if [ ! -d ${RNX_DIR} ]; then
    mkdir -p ${RNX_DIR}
fi

OBS_OPTS=" -x "${EXCL_GNSS}" -s -D -v -R3 -l -O BEL -c "${opts_timing}
NAV_OPTS=" -x "${EXCL_GNSS}" -v -R3 -l -O BEL -n P "${opts_timing}

# switch to the RINEX directory
cd ${RNX_DIR}

echo -e "\e[1;34mCreating RINEX observation file in \e[1;32m${RNX_DIR}\e[0m"
${SBF2RIN} ${OBS_OPTS} -f ${SBF_FN} 

echo -e "\e[1;34mCreating RINEX navigation file in \e[1;32m${RNX_DIR}\e[0m"
${SBF2RIN} ${NAV_OPTS} -f ${SBF_FN}
