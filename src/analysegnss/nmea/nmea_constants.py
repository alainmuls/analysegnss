# dict containing the Quality modes for NMEA messages
DICT_NMEA_PVT_QUALITY = {
    0: dict(desc="Invalid", color="red"),
    1: dict(desc="Stand-Alone PVT", color="cornflowerblue"),
    2: dict(desc="Differential PVT", color="darkcyan"),
    4: dict(desc="RTK Fixed", color="green"),
    5: dict(desc="RTK Float or PPP", color="orange"), # in NMEA PPP pvt qual is also indicated as RTK float 
    6: dict(desc="INS Dead Reckoning", color="purple"),
    7: dict(desc="Manual input mode", color="yellow"),
    8: dict(desc="Simulation mode", color="gray"),
}
