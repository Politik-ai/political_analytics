
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


"""
To calculate the lugar metric within a given time range:

-Get all bills proposed during time range
-Filter by party
-

Aggregate total sponsorships for bills put out by a party

Get proportion of sponsorships that were not of the party

Take ratio, and report!

Later will normalize. 

"""
def lugar_metric(session, time_range):

    parties = ["Democrat", "Independent", "Republican"]
    #print(time_range)

    lugar_in_range = {}
    for p in parties:
        #print(p)
        
        #Get bills sponsored by party within given time range
        party_bills = party_primary_sponsor_bills(session, p)
        bills_in_range = bill_bw_dates(session, *time_range, party_bills).with_entities(Bill.id)

        #print(f'Bill count by party {p}: {util.get_count(bills_in_range)}')
        


        #Get sponsorships from relevant bills
        sponsors = get_sponsors_from_bills(session, bills_in_range)


        num_sponsors = sponsors.count()
        #print('num sponsors in time range:')
        #print(num_sponsors)
        if num_sponsors == 0:
            lugar_in_range[p] = 0
            continue

        #ignoring party switches?


        #party_bills = session.query(Bill.id).\
        #        select_from(join(Sponsorship, Politician)).\
        #                filter(
        #                    Politician_Term.party == p, \
        #                    Politician_Term.start_date <= Bill_State.intro_date, \
        #                    Politician_Term.end_date >= Bill_State.intro_date, \
        #                    Sponsorship.sponsor_type == 'primary')\
        #                            .filter(Bill.id.in_(bills_in_range.subquery()))


        #print(util.get_count(party_bills))

        #rel_vote_politicians = session.query(Vote_Politician.id).\
        #    join(Vote).\
        #        filter(Vote.bill_id.in_(party_bills.subquery()))

        ##party_votes = session.query(Vote_Politician).\
        #    join(Politician_Term).\
        #        group_by(Politician_Term.party).\
        #            filter(Vote_Politician.id.in_(rel_vote_politicians))


        #print(party_votes.all())

        #Filter sponsorships by party (need to specify time range since politician parties are time specific)
        p_only_sponsors = party_only_sponsorships(session, sponsors, p, time_range)

        p_only_count = util.get_count(p_only_sponsors)
        #print('party only sponsors')
        #print(p_only_count)

        #Ratio of non-party sponsors compared to total sponsors
        if p_only_count > num_sponsors:
            print("PROBLEM")
        lugar_in_range[p] = (num_sponsors - p_only_count)/num_sponsors

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
    #print(f"Lugar Average: {ave_lugar}")
    print(lugar_in_range)

    return lugar_in_range


#Vote based metric
"""
Percentage of votes that are classified as receiving bipartisan support

EITHER

-Majority of both parties (forget independents for now) vote the same way

-Difference in support level is within given cutoff (eg. 20%)

Continuous version would be %votes across the aisle c/p to all votes taken (taken from each party then aggregated)

"""

def bipartisan_vote_metric(session, cutoff, time_range):

    parties = ["Democrat", "Independent", "Republican"]

    for p in parties:

        party_bills = party_primary_sponsor_bills(session, p)
        #Get bills in range
        bills_in_range = bill_bw_dates(session, *time_range, party_bills)
        
        rel_votes = votes_from_bills(session, bills_in_range)

        votes_in_range = votes_between_dates(session, time_range)

        pol_votes = pol_votes_from_party(session, votes_in_range, p)



if __name__ == "__main__":

    session = Session()

    dates = get_bill_state_date_ranges(session)
    ranges = util.discretized_by_months(*dates)
    for r in ranges:
        lugar_metric(session, r)

        