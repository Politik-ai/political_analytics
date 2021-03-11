
#Get all bills associated with each month
#For each chunk, perform bi-partisan metric
from init_db import *
from framework import *
import sys, os
from political_queries import *
import util 
import pandas as pd
from sqlalchemy import distinct, and_
from multiprocessing_base import thread_worker
sys.path.append(os.path.abspath('../data_collection/database_filler'))
from base import get_session

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
def lugar_metric(session, time_range, parties, bill_subset=None):

    #Formatted [range, party, metric]
    lugar_in_range = []
    for p in parties:
        
        #Get bills sponsored by party within given time range
        if bill_subset is not None:
            party_bills = party_primary_sponsor_bills(session, p, bill_subset)
        else:
            party_bills = party_primary_sponsor_bills(session, p)
            
        #print(f'num party bills: {util.get_count(party_bills)}')

        bills_in_range = bill_bw_dates(session, *time_range, party_bills)
     
        print(f'num bills in range: {bills_in_range.count()}')

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

    #print('all votes in range:')
    #print(vote_ids_in_range.all())
    #Items in format [vote_id, party, response, count]
    #Get all votes done in during a range
    #Get party proprtion of votes on both sides for each vote
    #Determine whether or not vote was "bipartisan" based on cutoff (or both majority)
    #Count number of bipartisan votes vs non -> ratio for period

    vote_data = session.query(Vote.id, Politician_Term.party, Vote_Politician.response, func.count(distinct(Vote_Politician.id)))\
        .join(Vote_Politician).join(Politician).join(Politician_Term)\
            .filter(Vote.id.in_(vote_ids_in_range.subquery()))\
                    .group_by(Vote.id, Vote_Politician.response, Politician_Term.party)\
                        .yield_per(10000)


    vote_data_df = pd.DataFrame(vote_data, columns=['vote_id', 'party', 'response', 'count'])

    num_bipartisan_votes = 0
    num_votes = 0
    total_votes_len = vote_ids_in_range.count()
    for vote_id in vote_ids_in_range:
        indv_vote_df = vote_data_df[vote_data_df['vote_id'] == vote_id]
        vote_info = {}
        for p in parties:
            total_votes = indv_vote_df.loc[((indv_vote_df['party'] == p) & (vote_data_df['vote_id'] == vote_id)), 'count'].sum()
            
            support_votes = indv_vote_df.loc[((indv_vote_df['party'] == p) & (indv_vote_df['response'] == 1) & (vote_data_df['vote_id'] == vote_id)), 'count'].sum()
            
            
            #NOTE: EOF found in one of the parties, unknown reason
            if total_votes == 0:
                continue

            #print(f"support: {support_votes}")
            #print(f"total: {total_votes}")
            support_ratio = support_votes/total_votes
            vote_info[p] = support_ratio
        
        if maxDiff(list(vote_info.values())) < cutoff or min(vote_info.values()) >= 0.5:
            num_bipartisan_votes += 1
        num_votes += 1
        print(f'Completed vote in range: {num_votes}/{total_votes_len}')

    return num_bipartisan_votes/num_votes

def get_all_topic_metrics(session, parties, time_ranges, vote_cutoff, db_location):

    topic_ids_name = get_all_topics(session).with_entities(Topic.id, Topic.name).all()
    pool = ThreadPool(processes = 4)

    spec_topic_bills = topic_bills(session, topic.id)
    topic_vote_metrics = []
    topic_lugar_metrics = []

    results = pool.starmap_async(thread_worker, db_location, [(metrics_over_range, db_location, [t[1], time_ranges, parties, vote_cutoff, topic_bills(session, t[0])]) for topic in topic_ids_name])

    results = results.get()
    
    final_results = [[],[]]
    for r in results:
        final_results[0].extend(r[0])
        final_results[1].extend(r[1])

    return final_results

def metrics_over_range(session, topic_name, time_ranges, parties, cutoff, bill_subset=None):
    
    lugar_metrics = []
    vote_metrics = []
    for t_range in time_ranges:
        vote_metrics.append([t_range[0], bipartisan_vote_metric(session, cutoff, t_range, parties)])
        lugar_metrics.extend(lugar_metric(session, t_range, parties))
        print(f"Completed range: {t_range}")

    #TODO:Save topic information

    return [vote_metrics, lugar_metrics]





if __name__ == "__main__":

    db_location = sys.argv[1]


    import seaborn as sns
    import matplotlib.pyplot as plt
    sns.set_theme(style="darkgrid")

    session = get_session(db_location)
    dates = get_bill_state_date_ranges(session)
    week_ranges = util.discretized_by_weeks(*dates)
    month_ranges = util.discretized_by_months(*dates)
    chosen_range = week_ranges

    vote_cutoff = 0.2

    all_lugars = []
    parties = ["Democrat", "Independent", "Republican"]

    vote_metrics = []
    for r in chosen_range:
        metric = bipartisan_vote_metric(session, vote_cutoff, r, ['Democrat', 'Republican'])
        if metric is not None:
            vote_metrics.append([r[0], metric])

    vote_metrics_df = pd.DataFrame(vote_metrics, columns=['date', 'bipartisanship_ratio'])
    vote_metrics_df.to_csv('113_only_vote_metrics.csv', index=False)


    i = 1
    num_ranges = len(chosen_range)
    for r in chosen_range:
        if i > 1:
            break
        range_lugar = lugar_metric(session, r, parties)
        all_lugars.extend(range_lugar)
        print(f"{i}/{num_ranges}")
        i += 1

    lugar_df = pd.DataFrame(all_lugars, columns=['date', 'party', 'lugar_score'])
    lugar_df.to_csv('113_only_lugar_metrics.csv', index=False)

    fix, axarr = plt.subplots(2, sharex=True)
    sns.lineplot(x='date', y='bipartisanship_ratio', data=vote_metrics_df, ax=axarr[0])
    sns.lineplot(x='date', y="lugar_score", hue="party", data=lugar_df, ax=axarr[1])
    
    figure = fix.get_figure()
    #fix.savefig("figure_name" + "_score" ".png")


    metrics_over_range(session, chosen_range, parties, vote_cutoff, db_location)



#Future plans
"""
-Seasonally adjust the economic metrics
-Do it for longer periods of time
-Specify topic (may parse out procedural votes which is helpful)
-Parse out weekly/monthly/yearly seasonal trends (potentially parsing out procedural things)
-Spend more time confirming code works as expected.

"""