import polars as pl

SBF_BLOCK_COLUMNS_BIN2ASC = {
    "MeasEpoch2": {
        pl.UInt32: ["TOW [0.001 s]"],
        pl.UInt16: ["WNc [w]", "MeasType", "Antenna ID", "SignalType", "LockTime [s]"],
        pl.String: ["SVID"],
        pl.Float64: ["CN0_dBHz [dB-Hz]", "PR_m [m]", "Doppler_Hz", "L_cycles [cyc]"],
    },
    "Meas3Ranges": {
        pl.Float32: ["TOW [s]"],
        pl.UInt16: ["WNc [w]", "LockTime [s]"],
        pl.String: ["SVID", "SignalType", "Antenna ID"],
        pl.Float64: ["PR [m]", "L [cyc]", "Doppler [Hz]", "C/N0 [dB-Hz]"],
    },
    "PVTCartesian2": {
        pl.Float64: [
            "X [m]",
            "Y [m]",
            "Z [m]",
            "Vx [m/s]",
            "Vy [m/s]",
            "Vz [m/s]",
            "COG [°]",
        ],
        pl.UInt32: [
            "TOW [0.001 s]",
        ],
        pl.UInt16: [
            "WNc [w]",
            "MeanCorrAge [0.01 s]",
        ],
        pl.UInt8: [
            "Type",
            "Error",
            "NrSV",
        ],
    },
    "PVTGeodetic2": {
        pl.Float64: [
            "Latitude [rad]",
            "Longitude [rad]",
            "Height [m]",
        ],
        pl.Float32: [
            "Undulation [m]",
            "COG [°]",
        ],
        pl.UInt32: [
            "TOW [0.001 s]",
            "SignalInfo",
        ],
        pl.UInt16: [
            "WNc [w]",
            "MeanCorrAge [0.01 s]",
        ],
        pl.UInt8: [
            "Type",
            "Error",
            "NrSV",
        ],
    },
    "PosCovCartesian1": {
        pl.Float32: [
            "Cov_xx [m²]",
            "Cov_yy [m²]",
            "Cov_zz [m²]",
            "Cov_bb [s²]",
        ],
        pl.UInt32: [
            "TOW [0.001 s]",
        ],
        pl.UInt16: [
            "WNc [w]",
        ],
    },
    "PosCovGeodetic1": {
        pl.Float32: [
            "Cov_latlat [m²]",
            "Cov_lonlon [m²]",
            "Cov_hgthgt [m²]",
        ],
        pl.UInt32: [
            "TOW [0.001 s]",
        ],
        pl.UInt16: [
            "WNc [w]",
        ],
    },
    "Comment1": {
        pl.UInt32: [
            "TOW [0.001 s]",
        ],
        pl.UInt16: [
            "WNc [w]",
            "CommentLn",
        ],
        pl.Utf8: ["Comment"],
    },
    "BaseStation1": {
        pl.UInt32: [
            "TOW [0.001 s]",
        ],
        pl.UInt16: ["WNc [w]", "BaseStationID"],
        pl.UInt8: [
            "BaseType",
            "Source",
            "Datum",
        ],
        pl.Float64: [
            "X [m]",
            "Y [m]",
            "Z [m]",
        ],
    },
}

# elif sbf_block == "PVTResiduals2":
#     keep_cols = [
#         "TOW [0.001 s]",
#         "WNc [w]",
#         "N",
#         "SVID",
#         "FreqNr",
#         "Type",
#         "MeasInfo",
#         "ResidualType",
#         "Pseudorange residuals",
#         "Carrier-phase residuals",
#         "Doppler residuals",
#         "Fixed ambiguity",
#         "Residual [m]",
#         "Residual [cyc]",
#         "Residual [m/s]",
#     ]
# elif sbf_block == "SatVisibility1":
#     keep_cols = [
#         "TOW [0.001 s]",
#         "WNc [w]",
#         "SVID",
#         "Azimuth_deg",
#         "Elevation_deg",
#         "RiseSet",
#         "SatelliteInfo",
#     ]
# elif sbf_block == "ReceiverTime":
#     keep_cols = [
#         "TOW [0.001 s]",
#         "WNc [w]",
#         "UTCYear [Y]",
#         "UTCMonth [month]",
#         "UTCDay [d]",
#         "UTCHour [h]",
#         "UTCMin [min.]",
#         "UTCSec [s]",
#         "DeltaLS [s]",
#     ]

SBF_BLOCK_COLUMNS_SBF2ASC = {
    "PVTCartesian2": [
        "0",
        "GPST [s]",
        "X [m]",
        "Y [m]",
        "Z [m]",
        "Vx [m/s]",
        "Vy [m/s]",
        "Vz [m/s]",
        "RxClockBias [s]",
        "RxClockDrift [s/s]",
        "NrSV",
        "PVT Mode",
        "MeanCorrAge [0.01 s]",
        "PVT Error",
        "COG [°]",
    ],
    "PVTGeodetic2": [
        "-1",
        "GPST [s]",
        "Latitude [rad]",
        "Longitude [rad]",
        "Height [m]",
        "Undulation [m]",
        "Vn [m/s]",
        "Ve [m/s]",
        "Vu [m/s]",
        "ClockBias [s]",
        "ClockDrift [s/s]",
        "NrSV",
        "PVT Mode",
        "MeanCorrAge [0.01 s]",
        "PVT Error",
        "COG [°]",
    ],
    "PosCovCartesian1": [
        "-2",
        "GPST [s]",
        "Cov_XX [m²]",
        "Cov_YY [m²]",
        "Cov_ZZ [m²]",
        "Cov_tt [s²]",
    ],
}
