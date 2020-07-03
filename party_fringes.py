#Use this to answer interesting questions that don't require ML
from init_db import *
from framework import *
from political_queries import *
from datetime import date
import yaml
import os

from contextlib import contextmanager
from multiprocessing import Pool as ThreadPool

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    #engine = create_engine('sqlite:///../data_collection/political_db.db')
    #Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

def thread_worker(f, args):
    # We're using the session context here.
    with session_scope() as session:
        f(session, *args)


#Given party, who will not vote with the party the most?
def party_fringe(party, rel_date = None):
    #Get average voting records of all politicians for party sponsored bills
    #which politician votes the most negative with that party. 
    party_bills = party_primary_sponsor_bills(party)


    party_pols = party_politicians(party)
    if not not rel_date:
        party_pols = filter_pols_by_congress(party_pols, rel_date)

    party_vote_results = {}
    party_ratios = []
    lowest_ratio = 1
    lowest_ratio_id = None
    lowest_ratio_name = None
    num_pols = len(party_pols.all())
    i = 0
    for pol in party_pols:
        i += 1
        print(f"{i}/{num_pols}")
        pol_bills = politician_bills(pol.id)
        relevant_bills = pol_bills.intersect(party_bills)
        party_votes = pol_votes_from_votes(votes_from_bills(relevant_bills), pol.id)
        pol_results = pass_stats(party_votes)
        total_votes = pol_results['aye'] + pol_results['no'] + pol_results['aqui']
        if total_votes == 0:
            continue
        party_vote_results[pol.id] = pol_results


        ratio = round(pol_results['aye']/total_votes,3)
        party_ratios.append([pol.first_name + " " + pol.last_name, ratio, total_votes])
        if ratio < lowest_ratio:
            lowest_ratio = ratio
            lowest_ratio_id = pol.id
            lowest_ratio_name = pol.first_name + " " + pol.last_name
        
    #print('Total party ratios:')

    def get_ratio(item):
        return item[1]

    party_ratios.sort(key=get_ratio)
    for r in party_ratios:
        #print(f"{r[0]}: {r[1]} (Sample size: {r[2]})")
        continue

    return party_ratios


def party_topic_fringe(session, party, topic, rel_date = None):
    #Get average voting records of all politicians for party sponsored bills
    #which politician votes the most negative with that party. 
    engine.dispose()
    party_bills = party_primary_sponsor_bills(session, party)
    party_topic_bills = topic_bills(session, topic, party_bills)

    party_pols = party_politicians(session, party)
    if not not rel_date:
        party_pols = filter_pols_by_congress(session, party_pols, rel_date)

    party_vote_results = {}
    lowest_ratio = 1
    party_ratios = []

    lowest_ratio_id = None
    lowest_ratio_name = None
    num_pols = len(party_pols.all())
    i = 0
    print(f'Getting data for topic: {topic}')
    for pol in party_pols:
        i += 1
        #if i > 15:
        #    break
        print(f"{i}/{num_pols}")
        pol_bills = politician_bills(session, pol.id)
        #print(f'Getting data for: {pol.first_name} {pol.last_name}: {len(pol_bills.all())}')
        relevant_bills = pol_bills.intersect(party_topic_bills)
        party_votes = pol_votes_from_votes(session, votes_from_bills(session, relevant_bills), pol.id)
        pol_results = pass_stats(party_votes)
        total_votes = pol_results['aye'] + pol_results['no'] + pol_results['aqui']
        if total_votes == 0:
            #print('No votes found')
            continue
        party_vote_results[pol.id] = pol_results
        
        ratio = round(pol_results['aye']/total_votes, 3)
        party_ratios.append([pol.first_name + " " + pol.last_name, ratio, total_votes])


    def get_ratio(item):
        return item[1]
    #print(f'Total vote dict size: {len(party_ratios)}')
    #print(party_ratios)
    party_ratios.sort(key=get_ratio)
    #if len(party_ratios) > 0:
     #   continue
        #print(f"{party_ratios[0][0]}: {party_ratios[0][1]} (Sample size: {party_ratios[0][2]})")
        
    return {topic: party_ratios} 




def get_all_topic_fringes_concurrently(party, rel_date, thread_number=11):
    session = Session()
    topics = get_all_topics(session)
    session.close()
    pool = ThreadPool(thread_number)
    results = pool.starmap(thread_worker, [(party_topic_fringe, [party, topic.id, rel_date]) for topic in topics])

    pool.close()
    pool.join()
    total_results = {}
    for r in total_results:
        total_results.update(r)
    
    print(total_results)

    return results


#party_fringe("Republican")
#party_fringe("Democrat", date(2014,2,1))
#session = Session()
#party_topic_fringe(session, "Republican", 1, date(2014,2,1))

result = get_all_topic_fringes_concurrently("Republican", date(2014,2,1))

with open('repub_topic_fringes.yaml', 'w') as outfile:
    yaml.dump(result, outfile, default_flow_style=True)

#Question: Given topic and party, which politician is most of fringe of voting
