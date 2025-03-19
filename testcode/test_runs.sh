clear; rtk_pvtgeod --sbf_ifn /home/amuls/GNSSData/USA_CA_2024/Ocotillo/rover/1342172Z.24_ -vvv --sd
clear; ppk_rnx2rtkp  --pos_ifn /home/amuls/cylab/SURVEYS/2024-10-01-Keiheuvel_Demo/rtkp/134200BEL_R_20242751023_01H_10Z_MO.pos -vvv
clear; plot_coords  --pos_ifn /home/amuls/cylab/SURVEYS/2024-10-01-Keiheuvel_Demo/rtkp/134200BEL_R_20242751023_01H_10Z_MO.pos -vvv --display --sd --mpl
clear; plot_coords --sbf_ifn /home/amuls/GNSSData/USA_CA_2024/Ocotillo/rover/1342172Z.24_ -vvv --display --sd --mpl --archive /tmp
clear; plot_coords --glab_ifn /home/amuls/GNSSData/2024-03-29-schaffen/20240329/glab/KMS000BEL_R_20240890943_03H_01S_MO_gal.glab -vvv --display --sd --mpl --archive /tmp
clear; rnxobs_csv  --obs_ifn /home/amuls/cylab/SURVEYS/2024-10-01-Keiheuvel_Demo/rnx/base00BEL_R_20242751022_01H_05S_MO.rnx -vvv
clear; rnxnav_csv  --nav_ifn /home/amuls/cylab/SURVEYS/2024-10-01-Keiheuvel_Demo/rnx/base00BEL_R_20242751021_01H_MN.rnx -vvv --gnss GREC
clear; rnxnav_csv --nav_ifn /home/amuls/cylab/TESTDATA/data2test/data/BRUX00BEL0_GREC.nav -vvv --gnss GREC
clear; rnxnav_csv --nav_ifn /home/amuls/cylab/TESTDATA/data2test/data/BRUX00BEL0_GREC.nav -vvv --gnss R
clear; rnxnav_csv --nav_ifn /home/amuls/cylab/TESTDATA/flepos/BERT/RX3/BERT00BEL_R_20243640700_41H_MN.rnx -vvv --gnss R
clear; rnx_csv --obs_ifn /home/amuls/cylab/SURVEYS/2024-10-01-Keiheuvel_Demo/rnx/base00BEL_R_20242751022_01H_05S_MO.rnx --nav_ifn /home/amuls/cylab/TESTDATA/data2test/data/BRUX00BEL0_GREC.nav -vvv --gnss GE
clear; glab_parser --glab_ifn /home/amuls/GNSSData/2024-03-29-schaffen/20240329/glab/KMS000BEL_R_20240890943_03H_01S_MO_gal.glab --section OUTPUT,SATSEL -vv
clear; sbfmeas_csv --sbf_ifn /home/amuls/cylab/TESTDATA/analysegnss_data/ROVR187J.23_ -vvv --archive /tmp
clear; sbfnav_csv  --sbf_ifn /home/amuls/cylab/TESTDATA/analysegnss_data/ROVR187J.23_ -vvv --archive /tmp --gnss GREC
clear; sbfnav_csv --sbf_ifn ~/GNSSData/20241001-KEIHEUVEL/base_sbf/BASE275Z.24_ -vvv --archive /tmp --gnss GREC
clear; sbfnav_csv --sbf_ifn ~/cylab/TESTDATA/MosaicX5/MoX3345Z.22_ -vvv --archive /tmp --gnss GREC
