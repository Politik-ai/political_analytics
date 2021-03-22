
#Get all bills associated with each month
#For each chunk, perform bi-partisan metric
from init_db import *
from framework import *
import sys, os
from political_queries import *
import util 
import pandas as pd
from sqlalchemy import distinct, and_
from multiprocessing_base import thread_worker, ThreadPool
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

Aggregate total sponsorships for bills put out by a party

Get proportion of sponsorships that were not of the party

Take ratio, and report!

Later will normalize. 

"""


def lugar_metric(session, time_range, parties, t_id=None):

    #Formatted [range, party, metric]
    lugar_in_range = []
    for p in parties:
        #print(f'party: {p}')
        
        party_bills = party_primary_sponsor_bills(session, p)
        #Get bills sponsored by party within given time range
        if t_id is not None:
            party_bills = topic_bills(session, t_id, party_bills)
            
        bills_in_range = bill_bw_dates(session, *time_range, party_bills)
     
        #Get sponsorships from relevant bills
        sponsors = get_sponsors_from_bills(session, bills_in_range)

        num_sponsors = sponsors.count()
        if num_sponsors == 0:
            #Skip datapoint if no data
            continue

        #Filter sponsorships by party (need to specify time range since politician parties are time specific)
        p_only_sponsors = party_only_sponsorships(session, sponsors, p, time_range)

        p_only_count = p_only_sponsors.count()

        #Ratio of non-party sponsors compared to total sponsors
        if p_only_count > num_sponsors:
            print("PROBLEM")
        lugar_in_range.append([time_range[0], p, (num_sponsors - p_only_count)/num_sponsors])

    if len(lugar_in_range) != 0:
        average_score = sum([l[2] for l in lugar_in_range])/len(lugar_in_range)
        lugar_in_range.append([time_range[0], 'Average', average_score])


    return lugar_in_range


"""
Percentage of votes that are classified as receiving bipartisan support
EITHER
-Majority of both parties (forget independents for now) vote the same way
-Difference in support level is within given cutoff (eg. 20%)

Continuous version would be %votes across the aisle c/p to all votes taken (taken from each party then aggregated)
"""
def bipartisan_vote_metric(session, cutoff, time_range, parties, topic_id=None):


    def maxDiff(a):
        if not a:
            return 0

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

    if topic_id:

        t_bills = topic_bills(session, topic_id).with_entities(Bill.id)

        vote_data = session.query(Vote.id, Politician_Term.party, Vote_Politician.response, func.count(distinct(Vote_Politician.id)))\
            .join(Vote_Politician).join(Politician).join(Politician_Term).join(Bill)\
                .filter(Vote.id.in_(vote_ids_in_range.subquery()))\
                    .filter(Bill.id.in_(t_bills.subquery()))\
                        .group_by(Vote.id, Vote_Politician.response, Politician_Term.party)\

    else:
        vote_data = session.query(Vote.id, Politician_Term.party, Vote_Politician.response, func.count(distinct(Vote_Politician.id)))\
            .join(Vote_Politician).join(Politician).join(Politician_Term).join(Bill)\
                .filter(Vote.id.in_(vote_ids_in_range.subquery()))\
                    .group_by(Vote.id, Vote_Politician.response, Politician_Term.party)\

    if vote_data.count() == 0:
        print('no votes found on topic during range')
        return None

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
                print('no pol votes found in vote')
                continue

            support_ratio = support_votes/total_votes
            vote_info[p] = support_ratio
        
        if maxDiff(list(vote_info.values())) < cutoff or min(vote_info.values()) >= 0.5 or max(vote_info.values()) <= 0.5:
            num_bipartisan_votes += 1
        num_votes += 1
        print(f'Completed vote in range: {num_votes}/{total_votes_len}')

    return num_bipartisan_votes/num_votes

def get_all_topic_metrics(time_ranges, parties, vote_cutoff, db_location, topic_ids_name=None):

    session = get_session(db_location)

    if not topic_ids_name:
        topic_ids_name = get_all_topics(session).with_entities(Topic.name, Topic.id).all()

    pool = ThreadPool(processes = 6)

    session.close()

    # results = []
    # for t_id, t_name in topic_ids_name:
    #     cur_result = metrics_over_range(session, db_location, t_name, time_ranges, parties, vote_cutoff, t_id)
    #     results.append(cur_result) 

    results = pool.starmap_async(thread_worker, [(metrics_over_range, db_location, [t_name, time_ranges, parties, vote_cutoff, t_id]) for t_name, t_id in topic_ids_name])


    results = results.get()
    
    final_results = [[],[]]
    for r in results:
        final_results[0].extend(r[0])
        final_results[1].extend(r[1])

    return final_results

def metrics_over_range(session, db_location, topic_name, time_ranges, parties, cutoff, t_id=None):

    save_location = "bipartisanship_results/topic_time_results/" 

    lugar_metrics = []
    vote_metrics = []
    range_ind = 0
    for t_range in time_ranges:
        vote_metrics.append([t_range[0], bipartisan_vote_metric(session, cutoff, t_range, parties, t_id)])
        #lugar_metrics.extend(lugar_metric(session, t_range, parties, t_id))

        range_ind += 1
        print(f"Completed range for {t_id}: {range_ind}/{len(time_ranges)}")

    #TODO:Save topic information
    
    print(f"Saving metrics for {topic_name}")

    #lugar_df = pd.DataFrame(lugar_metrics, columns=['date', 'party', 'lugar'])
    #lugar_df.to_csv(save_location + f"lugar_metric_{t_id}.csv")

    vote_metrics_df = pd.DataFrame(vote_metrics, columns=['date', 'vote_metric'])
    vote_metrics_df.to_csv(save_location + f"vote_metric_{t_id}.csv")
    
    return [topic_name, vote_metrics, lugar_metrics]




if __name__ == "__main__":

    db_location = sys.argv[1]

    import seaborn as sns
    import matplotlib.pyplot as plt
    sns.set_theme(style="darkgrid")

    session = get_session(db_location)
    dates = get_bill_state_date_ranges(session)
    week_ranges = util.discretized_by_weeks(*dates)
    month_ranges = util.discretized_by_months(*dates)
    year_ranges = util.discretized_by_years(*dates)
    chosen_range = month_ranges

    print(year_ranges)

    vote_cutoff = 0.2

    all_lugars = []
    parties = ["Democrat", "Republican"]

    vote_metrics = []
    for r in chosen_range:
        metric = bipartisan_vote_metric(session, vote_cutoff, r, parties)
        if metric is not None:
            vote_metrics.append([r[0], metric])

    vote_metrics_df = pd.DataFrame(vote_metrics, columns=['date', 'bipartisanship_ratio'])
    vote_metrics_df.to_csv('bipartisanship_results/vote_metrics_monthly.csv', index=False)

    i = 1
    num_ranges = len(chosen_range)
    for r in chosen_range:
        range_lugar = lugar_metric(session, r, parties)
        all_lugars.extend(range_lugar)
        print(f"{i}/{num_ranges}")
        i += 1

    lugar_df = pd.DataFrame(all_lugars, columns=['date', 'party', 'lugar_score'])
    lugar_df.to_csv('bipartisanship_results/lugar_metrics_monthly.csv', index=False)

    fix, axarr = plt.subplots(2, sharex=True)
    sns.lineplot(x='date', y='bipartisanship_ratio', data=vote_metrics_df, ax=axarr[0])
    sns.lineplot(x='date', y="lugar_score", hue="party", data=lugar_df, ax=axarr[1])
    
    figure = fix.get_figure()
    fix.savefig("metrics" + "_score" + "_monthly" + ".png")

    # topics_to_check = [('Health', 288),
    #     ('Health_care_coverage_and_access', 64),
    #     ('Health_care_costs_and_insurance', 245),
    #     ('Armed_forces_and_national_security', 1),
    #     ('Military_personnel_and_dependents', 99),
    #     ('International_affairs', 49),
    #     ('Higher_education', 360),
    #     ('Education', 92),
    #     ('Education_programs_funding', 93),
    #     ('Elementary_and_secondary_education', 94),
    #     ('Student_aid_and_colleg_ costs', 335),
    #     ('Crime_and_law_enforcement', 311),
    #     ('Taxation', 130)]

    # topic_results = get_all_topic_metrics(chosen_range, parties, vote_cutoff, db_location, topics_to_check)
