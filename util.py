

import calendar
import datetime

from init_db import *
from framework import *
import sys, os
from political_queries import *






#Return list of month ranges based on given start and end date
def discretized_by_months(earliest, latest):

    [first_month, first_year] = [earliest.month, earliest.year]
    [last_month, last_year] = [latest.month, latest.year]
    _ , last_day = calendar.monthrange(last_year, last_month)

    end_date = datetime.datetime(last_year, last_month, last_day)    
    cur_date = datetime.datetime(first_year, first_month, 1)
    discretizations = []

    while cur_date < end_date:
        cur_range = []
        cur_range.append(cur_date)
        _, month_end = calendar.monthrange(cur_date.year, cur_date. month)
        cur_date = cur_date.replace(day=month_end)
        cur_range.append(cur_date)


        next_month = ((cur_date.month) % 12) + 1
        if next_month == 1:
            next_year = cur_date.year + 1
        else:
            next_year = cur_date.year
        cur_date = cur_date.replace(day=1, month=next_month, year=next_year)

        discretizations.append(cur_range)

    return discretizations


def discretized_by_weeks(earliest, latest):

    [first_month, first_year] = [earliest.month, earliest.year]
    [last_month, last_year] = [latest.month, latest.year]
    _ , last_day = calendar.monthrange(last_year, last_month)

    end_date = datetime.datetime(last_year, last_month, last_day)    
    cur_date = datetime.datetime(first_year, first_month, 1)
    discretizations = []

    week_start = cur_date

    while week_start < end_date:

        week_end = week_start + datetime.timedelta(days=6)

        #next_month = ((cur_date.month) % 12) + 1
        #if next_month == 1:
        #    next_year = cur_date.year + 1
        #else:
        #    next_year = cur_date.year
        #cur_date = cur_date.replace(day=1, month=next_month, year=next_year)

        discretizations.append([week_start, week_end])
        week_start = week_end + datetime.timedelta(days=1)

    return discretizations



def get_count(q):
    count_q = q.statement.with_only_columns([func.count()]).order_by(None)
    count = q.session.execute(count_q).scalar()
    return count

