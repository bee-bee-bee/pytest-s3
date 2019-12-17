#!/usr/bin/env python
# coding=utf-8

import time


def get_current_time_str():
    return time.strftime('%Y%m%d%H%M%S', time.localtime())


def timestamp():
    return int(time.time())


def year_month_day():
    return time.strftime('%Y-%m-%d', time.localtime())


def year_month_day_hour_minute_second():
    return time.strftime('%Y/%m/%d/%H_%M_%S', time.localtime())
