#Determine sponsorship power of individuals
from political_queries import *
from init_db import *
from sqlalchemy import func
from datetime import date
from multiprocessing_base import*
import yaml


#For each pol:
"""
Percentage of sponsored bills that are successful, as well as number of sucessful sponsored bills (both matter)
For each topic and in general

Do this for regular/primary sponsor (some may make larger influences in one rather than the other, but others both)

Compare that to average pass rate for party bills.



Also separate voting b/w party. Some sponsors may generate strong party support, but no bipartisan. 

"""

def get_sponsorship_power_by_party_topic(session, polid, party, rel_dates, primary):

    if primary:
        bills = pol_primary_sponsored_bills(session, polid)
    else:
        bills = pol_sponsored_bills(session, polid)

    if rel_dates != None:
        bills = bill_bw_dates(session, *rel_dates, bills)    

    topics = get_all_topics(session)
    power_dict = {}

    for topic in topics:
        topic_bills = filter_bills_by_topic(session, bills, topic.id)
        topic_votes = votes_from_bills(session, topic_bills)
        #Filter votes by party
        pol_topic_votes = pol_votes_from_party(session, topic_votes, party)

        #Currently just taking pass percentage of all votes discarding no-votes
        power_dict[topic.name] = pass_stats_average(pass_stats(pol_topic_votes))

    return {polid: power_dict}



def get_sponsporship_power_in_party(session, party, rel_dates, primary, thread_number = 11):
    session = session()
    pols = party_politicians(session, party)
    session.close()
    pool = ThreadPool(processes = thread_number)
    results = pool.starmap_async(thread_worker, [(get_sponsorship_power_by_politician_topic, [pol.id, party, rel_dates, primary]) for pol in pols]).get()

    pool.close()
    pool.join()
    total_results = {}
    for r in results:
        total_results.update(r)
    
    return total_results

