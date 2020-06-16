
from init_db import *
from framework import Bill, Vote_Politician, Vote, Bill_State
from sqlalchemy import join

session = Session()



def get_politician_bills(polid):
    #Given a polid, find all votes that the politician voted on

    #Create a join with the vote_politician and bill_state_id, and return all bill_state_ids
    #convert bill_state_ids to bill_ids
    bill_query = session.query(Bill).join(Bill_State).join(Vote).join(Vote_Politician).filter(Vote_Politician.polid == polid)
    return bill_query.all()

def get_politician_topic_votes(polid):


    pol_bills = get_politician_bills(polid)

    topic_bills = session.

get_politician_bills('P000197')