#!/bin/bash 


OPTIONS=$(getopt -o hvf:m:b:e:p: -l help,sbf_fn,MSG_BLOCK,begin_epoch,end_epoch,out_dir -- "$@")

function usage {
    echo "$0 extracts SBF blocks from a SBF file"
    echo
    echo "usage: $0 [-h] -f SBF_fn [-r rnx_dir] [-x excl_GNSS]"
    echo "  -h              display help"
    echo "  -f SBF_fn       input SBF file"
    echo "  -m msg_block    SBF message to convert (cfr bin2asc -l)"
    echo "  -b begin_epoch  begin epoch (default: None, format: YYYY-MM-DD_HH:MM:SS or HH:MM:SS)"
    echo "  -e end_epoch    end epoch (default: None, format: YYYY-MM-DD_HH:MM:SS or HH:MM:SS)"
    echo "  -p out_dir      directory for output relative to SBF file directory (default .)"
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
OUT_DIR="."
BEGIN_EPOCH=""
END_EPOCH=""

while true; do
  case "$1" in
    -h|--help)          usage; ;;
    -f|--file)          SBF_FN="$2" ; shift ;;
    -m|--msg_block)     MSG_BLOCK="$2" ; shift ;;
    -b|--begin_epoch)   BEGIN_EPOCH="$2" ; shift ;;
    -e|--end_epoch)     END_EPOCH="$2" ; shift ;;
    -p|--out_dir)       OUT_DIR="$2" ; shift ;;
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

# Check if required options are provided and file exists
if [ -z "${SBF_FN}" ] || [ -z "${MSG_BLOCK}" ]; then
    echo -e "\e[1;31mError: Both -f (SBF_fn) and -m (MSG_BLOCK) are required options\e[0m"
    usage
fi

if [ ! -f "${SBF_FN}" ]; then
    echo -e "\e[1;31mError: Input file '${SBF_FN}' does not exist\e[0m"
    exit 5
fi

# locate sbf2rin and gfzrnx executables
BIN2ASC=`which bin2asc`
if [ -z "${BIN2ASC}" ]; then
    echo -e "\e[1;31mError: bin2asc executable not found in PATH\e[0m"
    exit 3
fi

# Get list of supported blocks and store in array
SUPPORTED_BLOCKS=$(bin2asc -l | grep -v '^$' | sed 's/^- //' | sort)
echo "MSG_BLOCK: ${MSG_BLOCK}"

# Check if specified mode is supported
if ! echo "${SUPPORTED_BLOCKS}" | grep -q "${MSG_BLOCK}$"; then
    echo -e "\e[1;31mError: Invalid mode '${MSG_BLOCK}'. Must be one of:\e[0m"
    echo "${SUPPORTED_BLOCKS}"
    exit 4
fi


# create the OUT_DIR if it does not exist
SBF_DIR=$(dirname "${SBF_FN}")  # Get the directory of the input SBF file
OUT_DIR="${SBF_DIR}/${OUT_DIR}"  # Combine paths to get absolute output directory
if [ ! -d ${OUT_DIR} ]; then
    mkdir -p ${OUT_DIR}
fi

# create the command line for bin2asc conversion
cmd_bin2asc="${BIN2ASC} -f ${SBF_FN} -n NaN -E -r -t"  # -A"

# check if verbose mode was specified
if [ "${VERBOSE}" = true ]; then
    cmd_bin2asc="${cmd_bin2asc} -v"
fi

# check for existence of BEGIN_TIME, if specified in correct format, than add to cmd_bin2asc
if [ -n "${BEGIN_EPOCH}" ]; then
    if [[ "${BEGIN_EPOCH}" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}:[0-9]{2}:[0-9]{2}$ ]]; then
        cmd_bin2asc="${cmd_bin2asc} -b ${BEGIN_EPOCH}"
    elif [[ "${BEGIN_EPOCH}" =~ ^[0-9]{2}:[0-9]{2}:[0-9]{2}$ ]]; then
        cmd_bin2asc="${cmd_bin2asc} -b ${BEGIN_EPOCH}"
    fi
fi
# check for existence of END_TIME, if specified in correct format, than add to cmd_bin2asc
if [ -n "${END_EPOCH}" ]; then
    if [[ "${END_EPOCH}" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}:[0-9]{2}:[0-9]{2}$ ]]; then
        cmd_bin2asc="${cmd_bin2asc} -e ${END_EPOCH}"
    elif [[ "${END_EPOCH}" =~ ^[0-9]{2}:[0-9]{2}:[0-9]{2}$ ]]; then
        cmd_bin2asc="${cmd_bin2asc} -e ${END_EPOCH}"
    fi
fi

# if the SBF block is Meas3Ranges add option  --extractGenMeas to cmd_bin2asc
if [ "${MSG_BLOCK}" = "Meas3Ranges" ]; then
    cmd_bin2asc="${cmd_bin2asc} --extractGenMeas"
fi

# add output directory to cmd_bin2asc
cmd_bin2asc="${cmd_bin2asc} -p ${OUT_DIR}"

# add message block to cmd_bin2asc
cmd_bin2asc="${cmd_bin2asc} -m ${MSG_BLOCK}"

echo -e "running: \e[1;32m${cmd_bin2asc}\e[0m"
# run the bin2asc command
${cmd_bin2asc}
exit $?
