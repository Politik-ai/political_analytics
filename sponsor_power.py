#Determine sponsorship power of individuals
from political_queries import *
from init_db import *
from sqlalchemy import func
from datetime import date
from multiprocessing_base import*
import yaml
sys.path.append(os.path.abspath('../data_collection/database_filler'))
from base import get_session

#For each pol:
"""
Percentage of sponsored bills that are successful, as well as number of sucessful sponsored bills (both matter)
For each topic and in general

Do this for regular/primary sponsor (some may make larger influences in one rather than the other, but others both)

Compare that to average pass rate for party bills.



Also separate voting b/w party. Some sponsors may generate strong party support, but no bipartisan. 

"""

#Get vote power for a specific sponsor 
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
    if bills.count() == 0:
        return {}

    for topic in topics:
        topic_bills = filter_bills_by_topic(session, bills, topic.id)

        if topic_bills.count() == 0:
            continue
        topic_votes = votes_from_bills(session, topic_bills)

        #When a bill is never even voted on, how should it be considered? 
        print(f"Num votes: {topic_votes.count()}")
        if topic_votes.count() == 0:
            continue

        #Filter votes by party
        pol_topic_votes = pol_votes_from_party(session, topic_votes, party)
        print(f"Num pol-votes: {pol_topic_votes.count()}")

        #Currently just taking pass percentage of all votes discarding no-votes
        power_dict[topic.name] = pass_stats_average(pass_stats(pol_topic_votes))

    return {polid: {'Name':pol_name, 'Topics':power_dict}}

#Get sponsorship vote power (affects on votes) for all pols in a party
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


#Get sponsorship agenda power for a specific person.
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

    if bills.count() == 0:
        return {}

    print(f"Polid: {polid}")
    for topic in topics:
        #print(topic.name)
        topic_bills = filter_bills_by_topic(session, bills, topic.id)
        num_bills = topic_bills.count()
        if num_bills == 0:
            print('no bills, skipping')
            continue
        num_votes = votes_from_bills(session, topic_bills).count()

        #When a bill is never even voted on, how should it be considered? 
        #Currently just taking pass percentage of all votes discarding no-votes
        power_dict[topic.name] = {'Votes':num_votes, 'Bills':num_bills}
        #print(power_dict)
        print('got results')
        
    return {polid: {'Name':pol_name, 'Topics':power_dict}}

#Get all sponsorship powers for all topics in a party
def get_sponsporship_agenda_power_in_party(party, rel_dates, primary, thread_number = 11):
    session = Session()
    pols = party_politicians(session, party)
    pols = filter_pols_by_date(session, pols, rel_dates[0]).all()
    print(f"Number of politicians: {len(pols)}")
    session.close()
    pool = ThreadPool(processes = thread_number)
    results = pool.starmap_async(thread_worker, [(get_sponsorship_agenda_power_by_party_topic, [pol.id, "test", rel_dates, primary]) for pol in pols])
    results = results.get()

    pool.close()
    pool.join()
    total_results = {}
    for r in results:
        total_results.update(r)
    
    return total_results


#Get sponsorship power for a given politician
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
    votes = votes.count()
    bills = bills.count()
    if bills == 0:
        ratio = 0
    else:
        ratio = votes/bills
    return {'id':polid, 'Name':pol_name, 'Ratio':ratio, 'Votes': votes, 'Bills': bills}

#Get general sponsorship power for all politicians in a party
def get_general_sponsorship_agenda_power(db_location, party, rel_dates, primary, thread_number = 12):
    session = get_session(db_location)
    pols = filter_pols_by_date(session, party_politicians(session, party), rel_dates[0]).all()
    session.close()
    pool = ThreadPool(processes = thread_number)
    results = pool.starmap_async(thread_worker, [(general_sponsorship_agenda_power, [pol.id, pol.first_name + " " + pol.last_name, rel_dates, primary]) for pol in pols]).get()

    pool.close()
    pool.join()
    total_results = {}

    def get_ratio(item):
        return item['Ratio']

    results.sort(key = get_ratio)

    return results

db_location = '../database_design/political_db.db'

#Testing results
result = get_general_sponsorship_agenda_power(db_location, 'Democrat', [date(2010,2,1), date(2019,2,1)], True)
with open('results/dem_general_sponsor_power.yaml', 'w+') as outfile:
    yaml.dump(result, outfile, default_flow_style=False)
result = get_general_sponsorship_agenda_power('Republican', [date(2010,2,1), date(2019,2,1)], True)
with open('results/gop_general_sponsor_power.yaml', 'w+') as outfile:
    yaml.dump(result, outfile, default_flow_style=False)
print('simple done')
# result = get_sponsporship_agenda_power_in_party('Democrat', [date(2013,2,1), date(2014,2,1)], True)
# with open('results/topic_specific_sponsor_power.yaml', 'w') as outfile:
#     yaml.dump(result, outfile, default_flow_style=False)