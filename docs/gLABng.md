---
attachments: [frequency-priority.png, signal-priority.png]
tags: [PRS/3PfD, PRS/gLABng]
title: gLABng
created: '2020-07-22T12:55:57.891Z'
modified: '2020-09-14T10:03:16.654Z'
---

# gLABng

## Introduction

I am attaching a link with the updated manual and the gLAB beta v6 (DPC or command line only). Please note that this version is a major overhaul in terms of processing capabilities, output data and processing speed (much faster). Input options have changed (but is fully backwards compatible) and the output messages have been expanded (there is also an option to print in v5 format). 

Before using the new version, please read the FAQ in the manual (or in command line with option __'-faq'__), and take a look at the new messages format, the new options or arguments format and the expanded INFO messages at the beginning of the output file. With this version you should be able to do any processing you want without having to split the data in the different files (note that a lot of the option can be configured on a satellite basis).

## RINEX & DCBs (Differential Code Bias)

gLAB is able to process any signal as long is in the RINEX observation file. The only limitations are the navigation messages and DCBs. gLAB reads only RINEX files, so it only supports the navigation messages defined up to RINEX 3.04, which for Galileo is the INAV E1-B INAV E5b and F/NAV E5a. If there is an specific navigation message, you can "convert" it to the same format of INAV RINEX navigation message format (which in principle shall not be a problem, as most of the fields required in the navigation message will be the same, just make sure to set the INAV flag in "Data sources" field.

The other limitation is the DCBs. In the case for Galileo C1A signal, gLAB will apply the E1-E5b DCB. For any Galileo E6 signal, no DCB is applied. For the DCBs, my recommendation is to disable all Galileo DCBs, and directly correct the DCB in the pseudorange measurement, which you can easily do with the option to add "User Added Error" to RINEX measurements (option __'-input:usererror'__, see file description with option __'-usererrorfile'__). Also set the option __'-pre:usererrorafter'__ to add the error after cycle-slip detection, so the correction does not interfere with the cycle-slips. Note that the correction must be given in metres, so DCB correction, as it is a frequency dependent term, it must converted to metres of the signal frequency, with the conversion factor (forigin)^2 / (fdestination)^2

Aside from these limitations, you can process any signal with any frequency or frequency combinations.

## My original configuration file

```
###################################################
#
#     gLAB - Version: 5.4.4
#     This is a self-generated configuration file.
#     It only contains the minimum options to change the defaults.
#     Created at: 09:54 on 06/07/2020
#
###################################################


###################################################
#     INPUT section
###################################################

-input:obs /home/amuls/GNSS/19134/rinex/COMB1340.19O
# -input:nav /home/amuls/GNSS/19134/rinex/COMB1340.19P
-input:nav /home/amuls/GNSS/19134/rinex/BRDC00IGS_R_20191340000_01D_MN.rnx

###################################################
#     PREPROCESS section
###################################################

-pre:setrecpos 4023741.230 309110.534 4922723.243
-pre:elevation 5
-pre:prealign
-pre:checkcodejumps
-pre:cs:datagap 40
-pre:cs:lli
-pre:cs:sf

###################################################
#     MODELLING section
###################################################

-model:iono no
-model:trop:nominal simple
-model:trop:mapping simple
-model:satclocks
-model:relclock
-model:satmovinflight
-model:earthrotinflight
-model:satphasecenter
-model:satphasevar
-model:sathealth
-model:allowmarginal


###################################################
#     FILTER section
###################################################

-filter:trop
-filter:meastype pseudorange
-filter:select G0-Code-1
-filter:refclkonlyorder GE
-filter:maxpdop 10

###################################################
#     OUTPUT section
###################################################

-output:file /home/amuls/GNSS/19134/COMB/NG-GPSN-SPP-SF/COMB1340-GPSN-SPP-SF-FULL-ng.out
-print:info
--print:cycleslips
-print:meas
-print:filter
--print:prefit
--print:postfit
--print:usererror
-print:meas:snr
-print:output
-print:satsel
-print:summary
-print:progress
-print:model


###################################################
#     End of self-generated parameters
###################################################

```


## Adjustments to configuration file

It is rare that you had so bad results from the navigation file. Did you try to compare the IGS file with yours with the gLAB comparison mode? This would show if there are indeed big differences (you can do it with the command 

```
gLAB -input:nav <file1> -input:nav <file2> -pre:sat 0,+E0"
```

Regarding the measurement selection, you are using the semi-automatic mode, as you provide the frequency to use but not the measurement in the filter (with the parameter 

```
-filter:select G0-Code-1
```

In this case, you set frequency 1 but the measurement to be selected by gLAB. Once you set a frequency, gLAB will not use another one (even if it makes the satellite to be discarded). The measurement will be selected later, when the INFO messages are printed, gLAB has only read the header of the observation file, which has the list of measurements in the file, but this list does not mean that all satellites will have those measurements, only some (or all) of them, so gLAB can not decide which one to use until it starts reading epoch data. The exact measurements used will appear in messages MODEL, PREFIT,  POSTFIT and EPOCHSAT messages.

The constellation file is a deprecated option (I forgot to mark it such) as it only supports GPS but in a single format type (these file types do not have a standard). Just don't use, it does not provide any advantage or meaningful data that can already be read from other files, such as an ANTEX file.

To use any frequency in the filter, you have two options: 

1. providing the frequency to the filter, for instance, to use GPS L1 and Galileo L5:  
 
    ```
    -filter:select G0-Code-1 -filter:select E0-Code-5
    ```

1. Setting the frequency priority list with the frequency you want on the first position (but without setting any measurement in the filter, as that option has preference), e.g. for Galileo to use first frequency 5: 

    ```
    -pre:freqorder E0-51
    ```

1. To set dual frequency combinations in the filter, you have to set the combination with its frequencies. For instance, to use the code iono-free L1-L2 for GPS and L1-L5 for Galileo, the command is:

    ```
    -filter:select G0-PC12 E0-PC15
    ```

1. To smooth any filter measurement, you need to tell gLAB which measurement has to be smoothed and with what measurement with option 

    ```
    -pre:smoothmeas
    ```

    For instance, to smooth with the carrier phase iono-free combinations the iono-free pseudoranges from the example above:

    ```
    -pre:smoothmeas G0-PC12 LC12 E0-PC15 LC15
    ```

    For the case of smoothing a pseudorange measurement. For instance, with this measurement in the filter:

    ```
    -filter:select G0-Code-1 -filter:select E0-Code-5
    ```


    To smooth them with carrier phases:

    ```
    -pre:smoothmeas G0-Code-1 phase-1 E0-Code-5 phase-5
    ```

    Note that you can make any combination for the filter and smoothing. gLAB does not check if the combination makes sense, it just checks whether the frequency exits in the given constellation and if there are measurements available in the observation file.

Regarding the DCBs, there is one option with each available DCB defined in the ICD of each constellation. Just let gLAB use the default options, as each DCB is for a specific measurement, and it will only apply it to its specific measurement

Some questions about your configuration:

- Why do you use a cycle-slip detector if you are not using any carrier phase in the filter?
- Why do you disable iono correction if it is one the most important delay source in single frequency navigation?
- Why do you estimate the troposphere residual in the filter if it is a very small term (few centimetres) and can only be estimated correctly in PPP mode? In SPP, it will only estimate noise
- Why do you use "simple" tropospheric nominal instead of the default "UNB-3" nominal in SPP?

## Mail 10 Sep 2020 from me

- I worked on using gLabng (I add 'ng' for 'new generation') and use as base the configuration file "GPSN-C1C-kinematic.cfg' (cfr attachment). I use the kinematic filter which if I am correct, allows standard a variation of 1 meter in either direction for the filter. Changing to static clearly improves the solution, but for now I prefer to consider the kinematic case.
- In this configuration file I use `-filter:select G0-C1C` which should be the same as `-filter:select G0-Code-1`, but when looking at results, they are very similar but not the same.
- If I want  a dual frequency solution, I use `-filter:select G0-PC12`. Do I understand correctly that you use "PC" for Pseudo-Range Combination on frequencies L1 and L2 in this case (while LC stands for Phase combination)? And would that be the same as using `-filter:select G0-C1C G0-C2L`, which code is being used when one specifies PC12 or PC15?
- I suppose that your answers for selecting the codes asked in previous paragraph also apply for the smoothing of code measurements which are possible by using either another code or a phase observable.
- In the produced 'out' file, the line starting with `INFO Station` gives a summary overview. The reported position and formal errors (these are standard deviations I suppose) do they represent a mean value of a weighted mean (if so what is the weight factor used)?Tx again for your time

## Mail Deimos 14 Sep 2020

If the receiver is fixed, static positioning will always improve the solution as it can propagate the coordinates from previous epoch to the next one with its confidence level. In gLAB v6 (your gLABng) it also supports randomwalk to improve accuracy for slow moving receivers (I'm not sure which is the speed limit for effectiveness of the randomwalk). The default configuration for randomwalk is for moving receivers at around 30Km/h, but you can change it with parameter `-filter:q:dr`, with the argument to provide to be the maximum speed of the vehicle in metres/s squared.

Regarding the standard variation, the default is a fixed weight with 1 m for single code measurements, 1 m for iono-free code combinations, 0.01 m for single carrier phase measurements and 0.03 m for iono-free carrier phase combinations. You can change the filter weight to different types (in function of the elevation or SNR, ...) and its values (with parameters `-filter:fixedweight`, `-filter:elevweight`, `-filter:sinelevweight`, `-filter:snrweight` and `-filter:snrelevweight`). All these options have their first argument the filter measurement to apply the weight (the same argument as in parameter `-filter:select`, although the subset of satellites may differ) and then the parameters to fix the weight.

The difference between `-filter:select G0-C1C ` and `-filter:select G0-Code-1` is that in the former you set the measurement to use, while in the latter you let gLAB decide which one to use according to its priority list and the available measurements in the observation file. The priority list is set with parameter `-pre:measorder` (and if you check the help of this parameter, you will see the default list), and this list is later reduced to the ones available in the observation file (keeping the order). For GPS frequency 1 for codes, the list is `C1P,C1W,C1C,C1Y,C1L,C1S,C1X,C1M`. As you can see, C1P and C1W have higher priority than C1C, so if any of them is available it will be selected first (which is what occurs in your case). Note that in SBAS it is hard-coded to use C1C, due to MOPS restrictions, but outside of SBAS, it uses the best measurements possible. The resulting priority list is printed in the messages `INFO PREPROCESSING Rover priority list for frequency`. See an screenshot below:

![Priority list signals](/home/amuls/Documents/amnotes/attachments/signal-priority.png "")
    
Note that there is also a priority list for the frequencies, set with parameter `-pre:freqorder`, which works the same way as for the measurements. The resulting order is printed in the `INFO PREPROCESSING Measurement frequency filling order` messages.  See an screenshot below:

![Priority list frequancies](/home/amuls/Documents/amnotes/attachments/frequency-priority.png "")

Both priority list (frequencies and measurements) can be set each other independently in a per satellite basis.
      
As you state, PC is the iono-free combination for codes and LC is the iono-free combination for carrier phases. To manually set the measurements for a iono-free combination, just add them with dashes later. For instance, for the PC with C1P,C2P, the parameter will be `G0-PC12-C1P-C2P`. The order of measurements and frequencies is not important as long as they match (for instance `G0-PC21-C1P-C2P` or `G0-PC12-C2P-C1P` will yield the same results, as gLAB will internally order it). When you provided the parameter `-filter:select G0-C1C G0-C2L`, you were telling the filter to use to C1C and C2L as single measurements in the filter. 

To smooth measurements, you have to use parameters `-pre:smooth` and `-pre:smoothmeas`. The former is to set the number of seconds for smoothing in the Hatch filter, and the latter to set which measurements in the filter do you want to smooth and with what do you want to smooth. Therefore, the first argument is the same as in `-filter:select` (like in the weight options) and the second argument has the same format as the first but without the subset of satellites to use. For instance, to use PC12-C1C-C2L smoothed with LC12-L1C-L2L, the parameter will be `-pre:smooth G0-PC12-C1C-C2L LC12-L1C-L2L`. Smoothing can be done with single of dual frequency measurements independently of the code measurement to be applied to (you can smooth with LC a single code measurement or vice-versa).
              
In the summary, there are no standard deviations computed. The errors computed are simply comparing gLAB results against the reference (the a priori position), which are accumulated to compute the percentiles (which can be somewhat interpreted as a sigma in the end). The last line of the summary is just printing the same values shown in the previous lines of the summary but in one line, so it is easy to parse and make plots, except for the position, which is the last one computed by gLAB.
    
Some more comments:
  - In the configuration file, you use `-pre:sat +G0,-E0`. I recommend you to use instead `-pre:sat 0,+G0`. The `0` without any sign unselects all satellites of all constellations, and then you add the full GPS constellation. This is the best way to go in case you have a full multi-constellations file and you only want to use GPS. In the same way, if you want to use only GPS and Galileo, the parameter would be `-pre:sat 0,+GE0`.
  - To check what measurements is using gLAB in the filter, print the "EPOCHSAT" (with option `-print:sat`) or "PREFIT" (with option `-print:prefit`)  messages.
    
I hope this mail clarifies your doubt. It may look that gLAB has too many options or is too wide, but it is necessary to account for the large amount of possibilities due to the multi-constellation and multi-frequency. Once you get the feeling of how it works, you will see that everything makes sense.
              
Regards, Deimos

P.S: I am attaching an updated version of gLAB with some bugs fixed, as well as the manual in PDF (you can check the version of the software by checking the first line of the output file when the INFO message is enabled).
