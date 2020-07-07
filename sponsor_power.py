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

def get_sponsorship_vote_power_by_party_topic(session, polid, pol_name, party, rel_dates, primary):

    if primary:
        bills = pol_primary_sponsored_bills(session, polid)
    else:
        bills = pol_sponsored_bills(session, polid)

    rel_dates = None
    if rel_dates != None:
        bills = bill_bw_dates(session, *rel_dates, bills)    

    topics = get_all_topics(session)
    power_dict = {}

    if len(bills.all()) == 0:
        return {}

    for topic in topics:
        topic_bills = filter_bills_by_topic(session, bills, topic.id)
        #print(f"Num topic bills: {len(topic_bills.all())}")

        if len(topic_bills.all()) == 0:
            continue
        topic_votes = votes_from_bills(session, topic_bills)

        #When a bill is never even voted on, how should it be considered? 
        print(f"Num votes: {len(topic_votes.all())}")
        if len(topic_votes.all()) == 0:
            continue

        #Filter votes by party
        pol_topic_votes = pol_votes_from_party(session, topic_votes, party)
        print(f"Num pol-votes: {len(pol_topic_votes.all())}")

        #Currently just taking pass percentage of all votes discarding no-votes
        power_dict[topic.name] = pass_stats_average(pass_stats(pol_topic_votes))

    return {polid: {'Name':pol_name, 'Topics':power_dict}}

def get_sponsporship_vote_power_in_party(party, rel_dates, primary, thread_number = 11):
    session = Session()
    pols = party_politicians(session, party)
    session.close()
    pool = ThreadPool(processes = thread_number)
    results = pool.starmap_async(thread_worker, [(get_sponsorship_vote_power_by_party_topic, [pol.id, pol.first_name + " " + pol.last_name, party, rel_dates, primary]) for pol in pols]).get()

    pool.close()
    pool.join()
    total_results = {}
    for r in results:
        total_results.update(r)
    
    return total_results


def get_sponsorship_agenda_power_by_party_topic(session, polid, pol_name, rel_dates, primary):
    if primary:
        bills = pol_primary_sponsored_bills(session, polid)
    else:
        bills = pol_sponsored_bills(session, polid)

    rel_dates = None
    if rel_dates != None:
        bills = bill_bw_dates(session, *rel_dates, bills)    

    topics = get_all_topics(session)
    power_dict = {}

    if len(bills.all()) == 0:
        return {}

    print(f"Polid: {polid}")
    for topic in topics:
        topic_bills = filter_bills_by_topic(session, bills, topic.id)
        num_bills = len(topic_bills.all())
        if num_bills == 0:
            continue
        num_votes = len(votes_from_bills(session, topic_bills).all())

        #When a bill is never even voted on, how should it be considered? 

        #Currently just taking pass percentage of all votes discarding no-votes
        power_dict[topic.name] = {'Votes':num_votes, 'Bills':num_bills}
        #print(f"Topic: {topic.name}, Bill: {num_bills}, Votes: {num_votes}")
    print(f"Polid: {polid} DONE")
    session.rollback()
    print('rolled back')
    return {polid: {'Name':pol_name, 'Topics':power_dict}}

def get_sponsporship_agenda_power_in_party(party, rel_dates, primary, thread_number = 1):
    session = Session()
    pols = party_politicians(session, party)
    pols = filter_pols_by_date(session, pols, rel_dates[0])
    #print(f"Number of politicians: {len(pols.all())}")
    session.close()
    pool = ThreadPool(processes = thread_number)
    results = pool.starmap_async(thread_worker, [(get_sponsorship_agenda_power_by_party_topic, [pol.id, pol.first_name + " " + pol.last_name, rel_dates, primary]) for pol in pols]).get()

    pool.close()
    pool.join()
    total_results = {}
    for r in results:
        total_results.update(r)
    
    return total_results



def general_sponsorship_agenda_power(session, polid, pol_name, rel_dates, primary):

    if primary:
        bills = pol_primary_sponsored_bills(session, polid)
    else:
        bills = pol_sponsored_bills(session, polid)

    rel_dates = None
    if rel_dates != None:
        bills = bill_bw_dates(session, *rel_dates, bills)    

    votes = votes_from_bills(session, bills)

    #Currently just taking pass percentage of all votes discarding no-votes

    return {polid:  {'Name':pol_name, 'Ratio':len(votes.all())/len(bills.all()), 'Votes': len(votes.all()), 'Bills': len(bills.all())}}


def get_general_sponsorship_agenda_power(party, rel_dates, primary, thread_number = 12):
    session = Session()
    pols = filter_pols_by_date(session, party_politicians(session, party), rel_dates[0])
    session.close()
    pool = ThreadPool(processes = thread_number)
    results = pool.starmap_async(thread_worker, [(general_sponsorship_agenda_power, [pol.id, pol.first_name + " " + pol.last_name, rel_dates, primary]) for pol in pols]).get()

    pool.close()
    pool.join()
    total_results = {}


    for r in results:
        total_results.update(r)
    
    return total_results

result = get_general_sponsorship_agenda_power('Democrat', [date(2013,2,1), date(2014,2,1)], True)
with open('results/general_sponsor_power.yaml', 'w') as outfile:
    yaml.dump(result, outfile, default_flow_style=False)
print('simple done')
result = get_sponsporship_agenda_power_in_party('Democrat', [date(2013,2,1), date(2014,2,1)], True)
with open('results/topic_specific_sponsor_power.yaml', 'w') as outfile:
    yaml.dump(result, outfile, default_flow_style=False)