#!/usr/bin/env python
# coding: utf-8

import sys
from datetime import datetime, timedelta, time
import bisect
from math import isnan
from typing import Tuple

__author__ = "amuls"


_LEAP_DATES = (
    (1981, 6, 30),
    (1982, 6, 30),
    (1983, 6, 30),
    (1985, 6, 30),
    (1987, 12, 31),
    (1989, 12, 31),
    (1990, 12, 31),
    (1992, 6, 30),
    (1993, 6, 30),
    (1994, 6, 30),
    (1995, 12, 31),
    (1997, 6, 30),
    (1998, 12, 31),
    (2005, 12, 31),
    (2008, 12, 31),
    (2012, 6, 30),
    (2015, 6, 30),
    (2016, 12, 31),
)

LEAP_DATES = tuple(datetime(ld[0], ld[1], ld[2], 23, 59, 59) for ld in _LEAP_DATES)

_SECS_IN_WEEK = 604800
_GPS_EPOCH = datetime(1980, 1, 6, 0, 0, 0)


def leap(dt: datetime) -> int:
    """
    Return the number of leap seconds since 1980-01-01

    bisect.bisect returns the index `dt` would have to be
    inserted to keep `LEAP_DATES` sorted, so is the number of
    values in `LEAP_DATES` that are less than `dt`, or the
    number of leap seconds.

    :param dt: datetime instance
    :return: leap seconds for the dt
    """
    # bisect.bisect returns the index `dt` would have to be
    # inserted to keep `LEAP_DATES` sorted, so is the number of
    # values in `LEAP_DATES` that are less than `dt`, or the
    # number of leap seconds.
    return bisect.bisect(LEAP_DATES, dt)


def gnss2dt(week: int, tow: float) -> datetime:
    """
    :param week: GPS week number, i.e. 1866
    :param secs: number of seconds since the beginning of `week`
    :return: GPS datetime instance
    """
    if isnan(week) or isnan(tow):
        return float("nan")
    else:
        date_before_leaps = _GPS_EPOCH + timedelta(seconds=week * _SECS_IN_WEEK + tow)
        return date_before_leaps

def dt2gnss(dt: str, dt_format: str) -> Tuple[int, float]:
    """
    This converts a dateetime instance to GPS week number and time of week
    
    args:
        dt (datetime): datetime object
        dt_format (str): datetime format (e.g. "%Y-%m-%d %H:%M:%S")
    returns:
        Tuple[int, float]: GPS week number and time of week
    """

    dt_obj = datetime.strptime(dt, dt_format)
    gps_seconds = (dt_obj - _GPS_EPOCH).total_seconds()
    wn, tow = divmod(gps_seconds, _SECS_IN_WEEK)
    
    return wn, tow

def gpsms2dt(week: int, towms: float) -> datetime:
    """
    :param week: GPS week number, i.e. 1866
    :param secs: number of milliseconds since the beginning of `week`
    :return: GPS datetime instance
    """
    if isnan(week) or isnan(towms) or towms == 4294967295:
        return float("nan")
    else:
        date_before_leaps = _GPS_EPOCH + timedelta(
            seconds=week * _SECS_IN_WEEK + towms / 1000
        )
        return date_before_leaps


def gnss2utc(week: int, tow: float) -> datetime:
    """
    :param week: GPS week number, i.e. 1866
    :param secs: number of seconds since the beginning of `week`
    :return: UTC datetime instance
    """
    # print(f"week = {week}  TOW={tow}")
    if isnan(week) or isnan(tow):
        return float("nan")
    else:
        date_before_leaps = _GPS_EPOCH + timedelta(seconds=week * _SECS_IN_WEEK + tow)
        return date_before_leaps - timedelta(seconds=leap(date_before_leaps))


def utc2gnss(utc: str, utc_parser: str) -> datetime:
    """
    utc2gnss converts a datetime string given the parsing format to a GNSS time

    :param utc: string representing a UTC time
    :param utc_parser: strin grepresenting how to parse the 'utc' datetime
    :return: GNSS dateime instance
    """
    dt = datetime.strptime(utc, utc_parser)
    date_before_leaps = _GPS_EPOCH + timedelta(seconds=dt.timestamp())
    return dt + timedelta(seconds=leap(date_before_leaps))


def seconds2gnss(seconds: float) -> datetime:
    """
    seconds2gnss converts seconds (from 6 jan 1980) to GNSS time
    """
    WkNr, tow = divmod(seconds, _SECS_IN_WEEK)
    return gnss2dt(week=WkNr, tow=tow)


def sod_to_time(sod: float) -> datetime.time:
    """convert seconds of day (sod) to datetime.time

    Args:
        sod (float): seconds of day

    Returns:
        datetime.time: time representation
    """
    # Convert seconds to a timedelta object
    time_delta = timedelta(seconds=sod)

    # Extract the hours, minutes, and seconds from the timedelta object
    hours, remainder = divmod(time_delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    microseconds = time_delta.microseconds

    # Create a datetime.time object
    time_object = time(
        hour=hours, minute=minutes, second=seconds, microsecond=microseconds
    )

    return time_object


def main(argv: list) -> None:
    """
    main procedure invoked if called directly
    """
    # cFuncName = str_yellow(os.path.basename(__file__)) + ' - ' + str_green(sys._getframe().f_code.co_name)

    print(f"gnss2dt(week=2087, tow=460800.0)   = {gnss2dt(week=2087, tow=460800.0)}")
    print(f"gnss2utc(week=2087, tow=460800.0)  = {gnss2utc(week=2087, tow=460800.0)}")
    print(
        f"utc2gnssutc=()'2020-01-10 07:59:42', utc_parser='%Y-%m-%d %H:%M:%S')   = {utc2gnss(utc='2020-01-10 07:59:42', utc_parser='%Y-%m-%d %H:%M:%S')}"
    )
    print(
        f"utc2gnss(utc='23032022-14:52:23.012', utc_parser='%d%m%Y-%H:%M:%S.%f') = {utc2gnss(utc='23032022-14:52:23.012', utc_parser='%d%m%Y-%H:%M:%S.%f')}"
    )

    print(f"gpsms2dt(week=2142, tow=122400000) = {gpsms2dt(week=2142, tow=122400000)}")
    print(f"gpsms2dt(week=2142, tow=125999000) = {gpsms2dt(week=2142, tow=125999000)}")


# Only run main if this file is called directly
if __name__ == "__main__":
    main(argv=sys.argv)
