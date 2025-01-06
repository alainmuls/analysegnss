#!/bin/bash
# Script to convert FLEPOS data to RX3 format

# Add proper error handling
set -e  # Exit on error

OPTIONS=$(getopt -o hvf:s:d:y:x:r: -l help,verbose,fp_dir,station,doy,year,excl_GNSS,rnx3_dir -- "$@")

function usage {
    echo "$0 converts FLEPOS RINEX v2 files to RINEX v3.x format"
    echo
    echo "usage: $0 [-h] -f fp_dir -s station -d DOY [-r rnx3_dir] [-x excl_GNSS]"
    echo "  -h              display help"
    echo "  -f fp_dir       flepos directory"
    echo "  -s station      FLEPOS station name"
    echo "  -d DOY          day of year"
    echo "  -y year         year"
    echo "  -x excl_GNSS    exclude GNSS (default: RSCJI)"
    echo "  -r rnx3_dir     relative directory for RINEX v3.x output (default fp_dir)"
    echo "  -v              verbose output"
    exit 1
}

# Define colors
BOLD='\033[1m'
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

MV=$(command -v mv)

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

# Define cleanup function at the start of script
cleanup() {
    # Return to original directory
    cd "${ORIG_DIR}"
    
    # Check if conversion was successful
    if [ "${CONVERSION_SUCCESS}" = true ]; then
        echo -e "${GREEN}Conversion successful - cleaning up logs${NC}"
        rm -f "${LOG_FILE}"
    else
        echo -e "${RED}Conversion had errors - keeping logs for review${NC}"
    fi
}
trap cleanup EXIT INT TERM

# set the default options
RNX3_DIR="."
EXCL_GNSS="RSCJI"

# Define valid characters
VALID_CHARS="GRECSJI"

# Validation function
validate_excl_gnss() {
    local input=$1
    for (( i=0; i<${#input}; i++ )); do
        char="${input:$i:1}"
        if [[ ! $VALID_CHARS =~ $char ]]; then
            echo -e "${RED}Error: Invalid character '$char' in EXCL_GNSS. Valid characters are: $VALID_CHARS${NC}"
            return 1
        fi
    done
    return 0
}

# get the mandatory inputs
while true; do
    case "$1" in
        -f|--fp_dir)
            FP_DIR="$2"
            shift 2
            ;;
        -s|--station)
            STATION="$2"
            shift 2
            ;;
        -d|--doy)
            DOY="$2"
            shift 2
            ;;
        -y|--year)
            YEAR="$2"
            shift 2
            ;;
        -r|--rnx3_dir)
            RNX3_DIR="$2"
            shift 2
            ;;
        -x|--excl_GNSS)
            EXCL_GNSS="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        --)
            shift
            break
            ;;
        *)
            echo "Internal error!"
            exit 1
            ;;
    esac
done

echo "FP_DIR: "${FP_DIR}
echo "STATION: "${STATION}
echo "DOY: "${DOY}
echo "RNX3_DIR: "${RNX3_DIR}
echo "EXCL_GNSS: "${EXCL_GNSS}
echo "VERBOSE: "${VERBOSE}

# locate the gfzrnx executable and warn if not found
if ! command -v gfzrnx &> /dev/null; then
    echo -e "${BOLD}${RED}Error: gfzrnx executable not found${NC}"
    echo "Please install gfzrnx or ensure it's in your PATH"
    exit 1
fi
# Store the path in a variable
GFZRNX_EXEC=$(command -v gfzrnx)
echo 'GFZRNX_EXEC: '${GFZRNX_EXEC}

# Check if the FLEPOS directory exists
if [ ! -d "${FP_DIR}" ]; then
    echo -e "${BOLD}${RED}Error: FLEPOS directory '${FP_DIR}' does not exist${NC}"
    exit 2
fi
# change to the FLEPOS directory
cd "${FP_DIR}"

# Check if the station name is provided
if [ -z "${STATION}" ]; then
    echo -e "${BOLD}${RED}Error: Station name is required${NC}"
    exit 3
fi
# Check if the day of year is provided
if [ -z "${DOY}" ]; then
    echo -e "${BOLD}${RED}Error: Day of year is required${NC}"
    exit 4
fi
# check if the year is provided (could be 4 chars or 2 chars, only need last 2 chars)
if [ -z "${YEAR}" ]; then
    echo -e "${BOLD}${RED}Error: Year is required${NC}"
    exit 5
fi
# check if the year is 4 chars long and reduce to last 2 digits
if [ ${#YEAR} -eq 4 ]; then
    YEAR=${YEAR:2}
fi
# check if the year is 2 chars long
if [ ${#YEAR} -ne 2 ]; then
    echo -e "${BOLD}${RED}Error: Year must be 2 or 4 characters long${NC}"
    exit 6
fi
# get the list of excluded GNSS codes from the EXCL_GNSS variable and check whether they belong to GRECSJI
if ! validate_excl_gnss "$EXCL_GNSS"; then
    exit 7
fi

# check if the FLEPOS directory RINEX observation files for the station and DOY exist
RNX_OBS_FILE="${STATION}${DOY}0.${YEAR}o"
if [ ! -f "${RNX_OBS_FILE}" ]; then
    echo -e "${BOLD}${RED}Error: Observation file '${RNX_OBS_FILE}' does not exist${NC}"
    exit 8
fi

# Check if the RINEX v3.x output directory exists, if not, create it
if [ ! -d "${RNX3_DIR}" ]; then
    mkdir -p "${RNX3_DIR}"
fi

# Temporarily disable exit on error
set +e

# Get new filename and perform rename operation
RX3_fn=$(eval "${GFZRNX_EXEC} -finp ${RNX_OBS_FILE} -nomren23 BEL,00")
ERR_CODE=$?

if [ $ERR_CODE -eq 0 ]; then
    echo -e "Renaming ${BLUE}${RNX_OBS_FILE}${NC} to ${GREEN}${RX3_fn}${NC}"
    ${MV} "${RNX_OBS_FILE}" "${RNX3_DIR}/${RX3_fn}"
    ERR_CODE=$?
fi

# Re-enable exit on error
set -e

if [ ${ERR_CODE} -eq 0 ]; then
    CONVERSION_SUCCESS=true
else
    CONVERSION_SUCCESS=false
fi


# # exit 9
# # gfzrnx -finp `ls -1 BERT3610.24[lngc]` -fout ::RX3::00,BEL -f
# # gfzrnx -finp BERT3610.24o -fout ::RX3::00,BEL