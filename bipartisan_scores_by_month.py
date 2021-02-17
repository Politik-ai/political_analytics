
#Get all bills associated with each month
#For each chunk, perform bi-partisan metric
from init_db import *
from framework import *
import sys, os
from political_queries import *
import util

"""
Bi-partisan metrics:

Luger Metric - works with bill-sponsorship (frequency in which opposite sided members attract co-sponsors)
I can do this for each and do the average?
Proportion of sponsors that are bi-partisan?


Vote based bi-partisan metric
-Whether of not a bill was bi-partisan
    -majority of both parties voted together (both yes or no)
    -OR percentage of party vote is within 20%

"""

session = Session()

dates = get_bill_state_date_ranges(session)
ranges = util.discretized_by_months(*dates)

def get_count(q):
    count_q = q.statement.with_only_columns([func.count()]).order_by(None)
    count = q.session.execute(count_q).scalar()
    return count


def lugar_metric(session, ranges):

    lugars = []
    parties = ["Democrat"]#, "Independent", "Republican"]
    all_sponsors = session.query(Sponsorship)

    print('all sponsorships')
    print(all_sponsors.count())
    for r in ranges[-4:]:
        lugar_in_range = {}
        for p in parties:
            print(p)
            print(r)
            
            party_bills = party_primary_sponsor_bills(session, p)
            #Get bills in range
            bills_in_range = bill_bw_dates(session, *r)

            print(f'Bill count by party: {get_count(bills_in_range)}')

            sponsors = get_sponsors_from_bills(session, bills_in_range)

            num_sponsors = sponsors.count()
            print('num sponsors:')
            print(num_sponsors)
            if num_sponsors == 0:
                lugar_in_range[p] = 0
                continue

            p_only_sponsors = party_only_sponsorships(session, sponsors, p, r)

            p_only_count = get_count(p_only_sponsors)
            print('party only sponsors')
            print(p_only_count)

            lugar_in_range[p] = (num_sponsors - p_only_count)/num_sponsors
        print(lugar_in_range)

        tot_lugar, num_valid_parties = [0,0]
        for p in parties:
            if lugar_in_range[p] != 0:
                tot_lugar += lugar_in_range[p]
                num_valid_parties += 1
        if num_valid_parties == 0:
            ave_lugar = -1
        else:    
            ave_lugar = tot_lugar/num_valid_parties
        lugar_in_range["Average"] = ave_lugar
        print(f"Lugar Average: {ave_lugar}")
        lugars.append(lugar_in_range)
    print('done!')




lugar_metric(session, ranges)