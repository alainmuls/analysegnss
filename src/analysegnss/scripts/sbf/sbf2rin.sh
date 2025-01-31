#!/bin/bash 

# Add proper error handling
set -e  # Exit on error

OPTIONS=$(getopt -o hvf:r:x:b:e: -l help,verbose,sbf_fn,rnx_dir,excl_GNSS,begin_epoch,end_epoch -- "$@")

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

eval set -- "${OPTIONS}"

# Store original directory
ORIG_DIR=$(pwd)
# Add after storing ORIG_DIR
trap 'cd "${ORIG_DIR}"' EXIT

# get the script name without extension
SCRIPT_NAME=$(basename "$0" .sh)

# Add at start of script
LOG_FILE="${ORIG_DIR}/${SCRIPT_NAME}_$(date +%Y%m%d_%H%M%S).log"
exec 1> >(tee -a "$LOG_FILE") 2>&1

cleanup() {
    cd "${ORIG_DIR}"
    # Remove log file only if both conversions succeeded
    if [ "${CONVERSION_SUCCESS:-false}" = true ] && [ -f "${LOG_FILE}" ]; then
        rm -f "${LOG_FILE}"
    fi
}
trap cleanup EXIT INT TERM


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

# Check if required options are provided and file exists
if [ -z "${SBF_FN}" ]; then
    echo -e "\e[1;31mError: Option -f (SBF_fn) is required\e[0m"
    usage
fi

if [ ! -f "${SBF_FN}" ]; then
    echo -e "\e[1;31mError: Input file '${SBF_FN}' does not exist\e[0m"
    exit 5
fi

# Add validation for EXCL_GNSS parameter to ensure only valid GNSS letters are used
if ! [[ "$EXCL_GNSS" =~ ^[RSCJIG]+$ ]]; then
    echo -e "\e[1;31mError: Invalid GNSS exclusion characters. Use only R,S,C,J,I,G\e[0m"
    exit 1
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
# SBF_DIR=$(dirname "${SBF_FN}")  # Get the directory of the input SBF file
readonly RNX_DIR=$(readlink -f "${ORIG_DIR}/${RNX_DIR}")  # Combine paths to get absolute output directory
if [ ! -d "${RNX_DIR}" ]; then
    mkdir -p "${RNX_DIR}"
fi

OBS_OPTS=" -x "${EXCL_GNSS}" -s -D -v -R3 -l -O BEL -c "${opts_timing}
NAV_OPTS=" -x "${EXCL_GNSS}" -v -R3 -l -O BEL -n P "${opts_timing}

# switch to the RINEX directory
# cd "${RNX_DIR}" || exit 4

# Add error checking for conversions
if ${SBF2RIN} ${OBS_OPTS} -f "${SBF_FN}"; then
    # move the output files to the RINEX directory
    CONVERSION_SUCCESS=true
    RNX_OBS_FILE=`ls -t | grep -v "sbf2rin.*\.log" | head -n 1`
    /bin/mv "${RNX_OBS_FILE}" "${RNX_DIR}"
    echo -e "Created \e[1;34m${RNX_OBS_FILE}\e[0m file in \e[1;32m${RNX_DIR}\e[0m"
else
    CONVERSION_SUCCESS=false
    echo -e "\e[1;31mError: Failed to create observation file\e[0m"
    exit 6
fi

if ${SBF2RIN} ${NAV_OPTS} -f "${SBF_FN}"; then
    # move the output files to the RINEX directory
    CONVERSION_SUCCESS=true
    RNX_NAV_FILE=`ls -t | grep -v "sbf2rin.*\.log" | head -n 1`
    /bin/mv "${RNX_NAV_FILE}" "${RNX_DIR}"
    echo -e "Created \e[1;34m${RNX_NAV_FILE}\e[0m file in \e[1;32m${RNX_DIR}\e[0m"
else
    CONVERSION_SUCCESS=false
    echo -e "\e[1;31mError: Failed to create navigation file\e[0m"
    exit 7
fi

# return the output file paths
echo "${RNX_OBS_FILE}"
echo "${RNX_NAV_FILE}"

# cleanup() {
#     echo "DEBUG: Cleanup function called" >&2
#     cd "${ORIG_DIR}"
#     if [ "${CONVERSION_SUCCESS:-false}" = true ] && [ -f "${LOG_FILE}" ]; then
#         echo "DEBUG: Removing log file ${LOG_FILE}" >&2
#         rm -f "${LOG_FILE}"
#     fi
# }
