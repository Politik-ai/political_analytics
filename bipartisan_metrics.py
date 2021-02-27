
#Get all bills associated with each month
#For each chunk, perform bi-partisan metric
from init_db import *
from framework import *
import sys, os
from political_queries import *
import util 
import pandas as pd
from sqlalchemy import distinct, and_

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
def lugar_metric(session, time_range, parties):

    #Formatted [range, party, metric]
    lugar_in_range = []
    for p in parties:
        
        #Get bills sponsored by party within given time range
        party_bills = party_primary_sponsor_bills(session, p)
        bills_in_range = bill_bw_dates(session, *time_range, party_bills).with_entities(Bill.id)
     
        #Get sponsorships from relevant bills
        sponsors = get_sponsors_from_bills(session, bills_in_range)

        num_sponsors = sponsors.count()
        if num_sponsors == 0:
            #Skip datapoint if no data
            continue

        #Filter sponsorships by party (need to specify time range since politician parties are time specific)
        p_only_sponsors = party_only_sponsorships(session, sponsors, p, time_range)

        p_only_count = util.get_count(p_only_sponsors)

        #Ratio of non-party sponsors compared to total sponsors
        if p_only_count > num_sponsors:
            print("PROBLEM")
        lugar_in_range.append([time_range[0], p, (num_sponsors - p_only_count)/num_sponsors])

    return lugar_in_range


#Vote based metric
"""
Percentage of votes that are classified as receiving bipartisan support

EITHER

-Majority of both parties (forget independents for now) vote the same way
-Difference in support level is within given cutoff (eg. 20%)

Continuous version would be %votes across the aisle c/p to all votes taken (taken from each party then aggregated)
#NOTE: How to determine procedural votes (usually %100, which is stupid)
    -Topics could handle that for us

"""
def bipartisan_vote_metric(session, cutoff, time_range, parties):


    def maxDiff(a):

        vmin = a[0]
        dmax = 0
        for i in range(len(a)):
            if (a[i] < vmin):
                vmin = a[i]
            elif (a[i] - vmin > dmax):
                dmax = a[i] - vmin
        return dmax

    vote_metrics_in_range = []

    vote_ids_in_range =  votes_between_dates(session, time_range).with_entities(Vote.id)
    num_votes = len(vote_ids_in_range.all())
    if num_votes == 0:
        return None

    #Items in format [vote_id, party, response, count]
    #Get all votes done in during a range
    #Get party proprtion of votes on both sides for each vote
    #Determine whether or not vote was "bipartisan" based on cutoff (or both majority)
    #Count number of bipartisan votes vs non -> ratio for period
    vote_data = session.query(Vote.id, Politician_Term.party, Vote_Politician.response, func.count(distinct(Vote_Politician.id)))\
            .join(Vote_Politician).join(Politician).join(Politician_Term)\
                .filter(Vote.id.in_(vote_ids_in_range.subquery()))\
                    .filter(Vote.vote_date.between(Politician_Term.start_date, Politician_Term.end_date))\
                        .group_by(Vote.id, Vote_Politician.response, Politician_Term.party).all()

    max_votes = 0
    for vd in vote_data:
        if vd[3] > max_votes:
            max_votes = vd[3]

    #print('max votes:')
    #print(max_votes)

    vote_data_df = pd.DataFrame(vote_data, columns=['vote_id', 'party', 'response', 'count'])

    #print(vote_data_df)
    num_bipartisan_votes = 0
    num_votes = 0
    for vote_id in vote_ids_in_range:
        indv_vote_df = vote_data_df[vote_data_df['vote_id'] == vote_id]
        vote_info = {}
        for p in parties:
            party_df = indv_vote_df[indv_vote_df['party'] == p]
            #print('party df')
            #print(party_df)
            total_votes = party_df['count'].sum()
            #print(total_votes)
            support = party_df[party_df['response'] == 1]
            support_votes = support['count'].sum()

            support_ratio = support_votes/total_votes
            vote_info[p] = support_ratio
            #print('support')
            #print(support)
        
        if maxDiff(list(vote_info.values())) < cutoff or min(vote_info.values()) >= 0.5:
            num_bipartisan_votes += 1
        num_votes += 1

    return num_bipartisan_votes/num_votes


if __name__ == "__main__":

    import seaborn as sns
    import matplotlib.pyplot as plt
    sns.set_theme(style="darkgrid")

    session = Session()

    dates = get_bill_state_date_ranges(session)
    week_ranges = util.discretized_by_weeks(*dates)
    month_ranges = util.discretized_by_months(*dates)
    chosen_range = week_ranges

    all_lugars = []
    parties = ["Democrat", "Independent", "Republican"]


    vote_metrics = []
    for r in chosen_range:
        metric = bipartisan_vote_metric(session, .2, r, ['Democrat', 'Republican'])
        if metric is not None:
            vote_metrics.append([r[0], metric])

    vote_metrics_df = pd.DataFrame(vote_metrics, columns=['date', 'bipartisanship_ratio'])

    print(vote_metrics_df)

    i = 1
    num_ranges = len(chosen_range)
    for r in chosen_range:
        range_lugar = lugar_metric(session, r, parties)
        all_lugars += range_lugar
        print(f"{i}/{num_ranges}")
        i += 1


    lugar_df = pd.DataFrame(all_lugars, columns=['date', 'party', 'lugar_score'])

    fix, axarr = plt.subplots(2, sharex=True)

    sns.lineplot(x='date', y='bipartisanship_ratio', data=vote_metrics_df, ax=axarr[0])
    sns.lineplot(x='date', y="lugar_score", hue="party", data=lugar_df, ax=axarr[1])
    plt.show()    


#Future plans
"""
-Seasonally adjust the economic metrics
-Do it for longer periods of time
-Specify topic (may parse out procedural votes which is helpful)
-Parse out weekly/monthly/yearly seasonal trends (potentially parsing out procedural things)

-Spend more time confirming code works as expected..

"""