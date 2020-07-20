#Compare prevelancy of topic sponsorship by state as well as vote record of topics by state
from .political_queries import *
from .init_db import *
from sqlalchemy import func
from datetime import date
from .multiprocessing_base import*
import yaml


#Get all data on topics, as in number of bills on each topic.
def get_overall_topic_data(session, rel_date = None):

    result = session.query(Topic.name, func.count(Topic.id)).join(Bill_Topic).join(Bill).group_by(Topic.id)

    topic_dict = {}
    nums = [r[1] for r in result]
    total_sum = sum(nums)

    for r in result:
        topic_dict[r[0]] = r[1]/total_sum
        #print(f"{r[0]}: {topic_dict[r[0]]}")
    return topic_dict


def get_topic_info_by_state(session, state, rel_dates = None):

    bills =  session.query(Bill).join(Sponsorship).join(Politician).join(Politician_Term)\
        .filter(Politician_Term.state == state).filter(Sponsorship.sponsor_type == 'primary')

    if rel_dates != None:
        bills = bill_bw_dates(session, *rel_dates, bills)


    bill_subquery = bills.subquery()
    b_id, bill_code, status, originating_body = tuple(bill_subquery.c)
    result = session.query(Topic.name, func.count(Topic.id)).join(Bill_Topic).join(Bill).join(bill_subquery, b_id == Bill.id).group_by(Topic.id)

    topic_dict = {}
    result = result.all()
    num_bills = result.count()
    for r in result:
        topic_dict[r[0]] = r[1]/num_bills
        #print(f"{r[0]}: {topic_dict[r[0]]}")
    print(f"{state}: {len(result)}")
    return {state: topic_dict}

def get_topic_info_for_all_states(rel_dates, thread_number = 11):
    session = Session()
    states = get_all_states(session)
    session.close()
    pool = ThreadPool(processes = thread_number)
    results = pool.starmap_async(thread_worker, [(get_topic_info_by_state, [state, rel_dates]) for state in states]).get()

    pool.close()
    pool.join()
    total_results = {}
    for r in results:
        total_results.update(r)
    
    return total_results

        
session = Session()
general_result = get_overall_topic_data(session)

state_specific_result = get_topic_info_for_all_states([date(2013,2,1), date(2014,2,1)])

state_specific_ratios = {}

for state in state_specific_result:


    state_politicians = session.query(Politician_Term).filter(Politician_Term.state == state).filter(Politician_Term.start_date <= date(2014,2,1), Politician_Term.end_date >= date(2014,2,1))
    num_pols = state_politicians.count()
    
    state_results = state_specific_result[state]
    state_ratios = {}
    for topic in state_results:
        state_ratios[topic] = state_results[topic]/(general_result[topic]*num_pols)
    state_specific_ratios[state] = state_ratios

with open('topic_ratios_by_state_compared_to_general.yaml', 'w') as outfile:
    yaml.dump(state_specific_ratios, outfile, default_flow_style=False)