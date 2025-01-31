#!/bin/bash

function show_usage()
{
    printf "Usage: $0 [options [parameters]]\n"
    printf "\n"
    printf "Options:\n"
    printf " -f|--file, path to logfile\n"
    printf " -s|--satsys, satellite system (select out of G, R, E, J, C, I, S)\n"
    printf " -t|--time, time of logging (format y/m/d h:m:s)\n"
    printf " -l|--logf, logging format of data 'RTCM3, SBF, ubx'\n"
    printf " -h|--help, Print help\n"
}

if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]] || [[ $# -lt 5 ]]; then
    show_usage
    exit 0
else
    while [[ $# -gt 0 ]]; do
        key="$1"
        case $key in
            -f|--file)
            fn_path="$2"
            shift # past argument
            shift # past value
            ;;
            -s|--satsys)
            satsys="$2"
            shift # past argument
            shift # past value
            ;;
            -t|--time)
            time="$2"
            shift # past argument
            shift # past value
            ;;
            -l|--logf)
            logformat="$2"
            shift # past argument
            shift # past value
            ;;
            *)    # unknown option
            echo "Unknown option provided"
            show_usage
            exit 1
            ;;
        esac
    done
fi

# echo "fn_path = ${fn_path}"
# split file_name into path and filename
path_name=$(dirname "${fn_path}")
# echo "path_name = ${path_name}"
file_name=$(basename "${fn_path}")
# echo "file_name = ${file_name}"

# locate the convbin executable
CONVBIN=$(which convbin)
# check whether convbin is available
if [ -z "${CONVBIN}" ]; then
    echo "convbin not found"
    exit 1
# else
#     echo "CONVBIN = ${CONVBIN}"
fi

# create names of resulting OBS and NAV files
obs_name="${file_name%.*}_${satsys}.obs"
nav_name="${file_name%.*}_${satsys}.nav"
# echo "obs_name = ${obs_name}"
# echo "nav_name = ${nav_name}"

# change to directory where the RTCM3 file is located
cd ${path_name}

# create options for all satellite systems to elimante except for satsys
# G: GPS, R: GLONASS, E: Galileo, J: QZSS, C: BeiDou, I: IRNSS, S: SBAS
satsys_opt=""
for gnss in G R E J C I S; do
    # echo "gnss = ${gnss} | ${satsys}"
    if [[ "${satsys}" != *"${gnss}"* ]]; then
        satsys_opt+="-y ${gnss} "
    fi
done
# echo "satsys_opt = ${satsys_opt}"

echo "time=${time}"
# convert RTCM3 file to RINEX 3.03
if [ ! -z "$time" ]; then

    echo "Running: ${CONVBIN} -r ${logformat} -tr ${time} -v 3.03 -od -os -ot -oi ${satsys_opt} ${file_name} -o ${obs_name} -n ${nav_name}"
    ${CONVBIN} -r ${logformat} -tr ${time} -v 3.03 -od -os -ot -oi ${satsys_opt} ${file_name} -o ${obs_name} -n ${nav_name}
else
    echo "Running: ${CONVBIN} -r ${logformat} -v 3.03 -od -os -ot -oi ${satsys_opt} ${file_name} -o ${obs_name} -n ${nav_name}"
    ${CONVBIN} -r ${logformat} -v 3.03 -od -os -ot -oi ${satsys_opt} ${file_name} -o ${obs_name} -n ${nav_name}
fi
