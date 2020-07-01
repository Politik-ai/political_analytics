#Use this to answer interesting questions that don't require ML
from init_db import *
from framework import *
from political_queries import *
from datetime import date
import yaml
import os


#Imports for multiprocessing
from multiprocessing.dummy import Pool as ThreadPool
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker



def multiprocessing_init():
    engine = create_engine('sqlite:///../data_collection/political_db.db', echo=False)
    session_factory = sessionmaker(bind=engine)

    Session = scoped_session(session_factory)


    numbers = [1,2,3]
    work_parallel(numbers, 8)

    Session.remove()


def thread_worker(number):
    f1(number)

def f1(number):
    session = Session()

def work_parallel(numbers, thread_number=4):
    pool = ThreadPool(thread_number)
    results = pool.map(thread_worker)





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


def party_topic_fringe(party, topic, rel_date = None):
    #Get average voting records of all politicians for party sponsored bills
    #which politician votes the most negative with that party. 
    party_bills = party_primary_sponsor_bills(party)

    party_topic_bills = topic_bills(topic, party_bills)


    party_pols = party_politicians(party)
    if not not rel_date:
        party_pols = filter_pols_by_congress(party_pols, rel_date)

    party_vote_results = {}
    lowest_ratio = 1
    party_ratios = []

    lowest_ratio_id = None
    lowest_ratio_name = None
    num_pols = len(party_pols.all())
    i = 0
    for pol in party_pols:
        i += 1
        #print(f'Getting data for: {pol.first_name} {pol.last_name}')
        print(f"{i}/{num_pols}")
        pol_bills = politician_bills(pol.id)
        relevant_bills = pol_bills.intersect(party_topic_bills)
        party_votes = pol_votes_from_votes(votes_from_bills(relevant_bills), pol.id)
        pol_results = pass_stats(party_votes)
        total_votes = pol_results['aye'] + pol_results['no'] + pol_results['aqui']
        if total_votes == 0:
            continue
        party_vote_results[pol.id] = pol_results

        ratio = round(pol_results['aye']/total_votes, 3)
        party_ratios.append([pol.first_name + " " + pol.last_name, ratio, total_votes])

        #print(ratio)
        if ratio < lowest_ratio:
            lowest_ratio = ratio
            lowest_ratio_id = pol.id
            lowest_ratio_name = pol.first_name + " " + pol.last_name
        
    #print('Total party dict:')

    def get_ratio(item):
        return item[1]

    party_ratios.sort(key=get_ratio)
    for r in party_ratios:
        #print(f"{r[0]}: {r[1]} (Sample size: {r[2]})")
        continue

    return party_ratios 


def get_all_topic_fringes(party, rel_date = None):

    topics = get_all_topics()
    most_fringe = {}
    num_topics = len(topics)
    if not os.path.exists('repub_topic_fringes.yaml'):
        os.mknod('repub_topic_fringes.yaml')
    i = 0
    for t in topics:

        with open('repub_topic_fringes.yaml', 'r') as yamlfile:
            cur_yaml = yaml.safe_load(yamlfile)
            if not cur_yaml:
                cur_yaml = {}
        if t.name in cur_yaml:
            print(f'{t.name} already done')
            continue
        i += 1
        print(f"{i}/{num_topics}")
        fringe =  party_topic_fringe(party, t.id, rel_date)
        if not fringe:
            continue
        most_fringe[t.name] = fringe[0]

        cur_yaml[t.name] = fringe[0]
        print('saving to data')
        with open('repub_topic_fringes.yaml', 'w') as yamlfile:
            yaml.safe_dump(cur_yaml, yamlfile)

        print(f"{t.name}: {most_fringe[t.name]}")

    return most_fringe



#party_fringe("Republican")
#party_fringe("Democrat", date(2014,2,1))

#party_topic_fringe("Republican", 1, date(2014,2,1))

result = get_all_topic_fringes("Republican", date(2014,2,1))

with open('repub_topic_fringes.yaml', 'w') as outfile:
    yaml.dump(result, outfile, default_flow_style=True)

    #given bills not sponsored by party, which politician is most likely to vote yes on them. 

#Question: Given topic and party, which politician is most of fringe of voting
