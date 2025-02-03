#!/bin/bash
# Script to convert FLEPOS data to RX3 format

# Add proper error handling
set -e  # Exit on error

OPTIONS=$(getopt -o hvf:s:d:y:r: -l help,verbose,fp_dir,station,doy,year,rnx3_dir -- "$@")

function usage {
    echo "$0 converts FLEPOS RINEX v2 files to RINEX v3.x format"
    echo
    echo "usage: $0 [-h] -f fp_dir -s station -d DOY [-r rnx3_dir]"
    echo "  -h              display help"
    echo "  -f fp_dir       flepos directory"
    echo "  -s station      FLEPOS station name"
    echo "  -d DOY          day of year"
    echo "  -y year         year"
    # echo "  -x excl_GNSS    exclude GNSS (default: RSCJI)"
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
TOUCH=$(command -v touch)
RM=$(command -v rm)

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
EXCL_GNSS="SJI"

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
        # -x|--excl_GNSS)
        #     EXCL_GNSS="$2"
        #     shift 2
        #     ;;
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
    # ${TOUCH} "${RX3_fn}"
    echo "RNX3_DIR: "${RNX3_DIR}
    ${MV} "${RNX_OBS_FILE}" "${RNX3_DIR}/${RX3_fn}"
    ${RM} "${RX3_fn}"
    ERR_CODE=$?
fi

# Re-enable exit on error
set -e

# combine the RINEX navigation files for the station and DOY and selected GNSS
# Define GNSS system mappings
declare -A GNSS_MAP=(
    [G]="n"  # GPS
    [R]="g"  # GLONASS (l for Legacy)
    [E]="l"  # Galileo
    [C]="c"  # BeiDou
    [S]="s"  # SBAS
    [J]="j"  # QZSS
    [I]="i"  # IRNSS/NavIC
)

# Validation function using the mapping
validate_excl_gnss() {
    local input=$1
    for (( i=0; i<${#input}; i++ )); do
        char="${input:$i:1}"
        if [[ ! ${GNSS_MAP[$char]+_} ]]; then
            echo -e "${RED}Error: Invalid character '$char'. Valid characters are: ${!GNSS_MAP[*]}${NC}"
            return 1
        fi
    done
    return 0
}

# Get non-excluded systems
get_included_systems() {
    local excluded="$1"
    local included=""
    
    for sys in "${!GNSS_MAP[@]}"; do
        if [[ ! $excluded =~ $sys ]]; then
            included+="${GNSS_MAP[$sys]}"
        fi
    done
    echo "$included"
}

# Usage example
GNSS_NAV_EXT=$(get_included_systems "$EXCL_GNSS")
echo "Included GNSS systems (navigation files): ${GNSS_NAV_EXT}"

# Temporarily disable exit on error
set +e

# Get the list of RINEX navigation files for the station and DOY
# Initialize array if not already done
RINEX_NAV_FILES=()
for (( i=0; i<${#GNSS_NAV_EXT}; i++ )); do
    nav_type="${GNSS_NAV_EXT:$i:1}"
    # echo "nav_type: ${nav_type} | ${STATION}${DOY}0.${YEAR}${nav_type}"
    # RINEX_NAV_FILES=$(find . -maxdepth 1 -type f -name "${STATION}${DOY}0.${YEAR}${nav_type}")
    RINEX_NAV_FILES+=("${STATION}${DOY}0.${YEAR}${nav_type}")
done
echo -e "Combining RINEX navigation files: ${BLUE}${RINEX_NAV_FILES[*]}${NC}"
ERR_CODE=0

if [ ${ERR_CODE} -eq 0 ]; then
    # Combine the RINEX navigation files
    echo "Running "${GFZRNX_EXEC}" -finp "${RINEX_NAV_FILES[@]}" -no_nav_stk -fout ::RX3::00,BEL -version_out 3.04 2> /tmp/gfzrnx.log"
    ${GFZRNX_EXEC} -finp ${RINEX_NAV_FILES[@]} -no_nav_stk -fout ::RX3::00,BEL -version_out 3.04 2> /tmp/gfzrnx.log
    ERR_CODE=$?
fi

# Re-enable exit on error
set -e

if [ $ERR_CODE -le 1 ]; then
    latest_rnx=$(ls -t *.rnx | head -n1)
    echo -e "Combined ${BLUE}${RINEX_NAV_FILES[*]}${NC} to ${GREEN}${latest_rnx}${NC}"
    ${MV} "${latest_rnx}" "${RNX3_DIR}/${latest_rnx}"
    ERR_CODE=$?
fi

# Check if the conversion was successful and perform cleanup
if [ ${ERR_CODE} -eq 0 ]; then
    CONVERSION_SUCCESS=true
else
    CONVERSION_SUCCESS=false
fi
