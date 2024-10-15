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

if [ $? -ne 0 ]; then
  echo "getopt error"
  exit 1
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
GFZRNX=`which gfzrnx`
RM=/usr/bin/rm

# Extract directory
SBF_DIR=${SBF_FN%/*}
# Extract filename with extension
SBF_FILE=${SBF_FN##*/}
# Extract filename without extension
FILENAME=${SBF_FILE%.*}
# Extract extension
EXT=${SBF_FILE##*.}

# create the RNX_DIR if it does not exist
if [ ! -d ${RNX_DIR} ]; then
    mkdir -p ${RNX_DIR}
fi

SBF2RINOBSOPTS=" -x "${EXCL_GNSS}" -s -D -v -R3 -l -O BEL"
RNX_OBS=${FILENAME%.*}.obs

SBF2RINNAVOPTS=" -x "${EXCL_GNSS}" -v -R3 -l -O BEL -n P"
RNX_NAV=${FILENAME%.*}.nav

# switch to the RINEX directory
cd ${RNX_DIR}

echo -e "\e[1;34mCreating RINEX observation file \e[1;32m${RNX_DIR}/${RNX_OBS}\e[0m"
${SBF2RIN} ${SBF2RINOBSOPTS} -f ${SBF_DIR}/${SBF_FILE} -o ${RNX_DIR}/${RNX_OBS}
${GFZRNX} -f -finp ${RNX_DIR}/${RNX_OBS} -fout ::RX3::00,BEL 
# if success remove the first RNX_OBS file
if [ $? -eq 0 ]; then
    ${RM} ${RNX_OBS}
fi

echo -e "\e[1;34mCreating RINEX navigation file \e[1;32m${RNX_DIR}/${RNX_NAV}\e[0m"
${SBF2RIN} ${SBF2RINNAVOPTS} -f ${SBF_DIR}/${SBF_FILE} -o ${RNX_DIR}/${RNX_NAV} -n P
${GFZRNX} -f -finp ${RNX_DIR}/${RNX_NAV} -fout ::RX3::00,BEL 
# if success remove the first RNX_OBS file
if [ $? -eq 0 ]; then
    ${RM} ${RNX_NAV}
fi
