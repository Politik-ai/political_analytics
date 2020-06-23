
from init_db import *
from framework import *
from sqlalchemy import join
session = Session()


#BASIC QUERIES -----------------------------------------------------
def politician_bills(polid):
    bill_query = session.query(Bill).join(Bill_State).join(Vote).join(Vote_Politician).filter(Vote_Politician.polid == polid)
    return bill_query

def topic_bills(topic_id):
    return session.query(Bill).join(Bill_Topic).join(Topic).filter(Topic.id == topic_id)


def dummy_query(dummy_id):
    return "u dummy"

#Given polid, return all votes by that politician on a certain topic
def politician_topic_bills(polid, topic_id):
    pol_bills = politician_bills(polid)
    topic_bills = topic_bills(topic_id)
    pol_topic_bills = pol_bills.union(topic_bills)
    #topic_bills = session.query(Bill).join(pol_bills, Bill.id == pol_bills.c.id).join(Bill_Topic).join(topic_bills, Topic.id == topic_bills.c.id)
    return pol_topic_bills

#return all bill of a given party
def party_bills(party):
    party_bills = session.query(Bill).join(Sponsorship).join(Politician).filter(Politician.party == party)
    return party_bills

#Returns bills between given dates
def bills_bw_dates(before_date, after_date):
    return session.query(Bill).join(Bill_State).filter(Bill_State.intro_date.between(before_date,after_date))

#BASIC GETS --------------------------------------------------------
def get_all_politician():
    return session.query(Politician.id).all()
def get_all_topics():
    return session.query(Topic.id).all()



#COMBINATION QUERIES -----------------------------------------------
def politician_topic_votes(polid, topic_id):
    topic_bills = politician_topic_bills(polid, topic_id).subquery()
    topic_votes = session.query(Vote_Politician).filter(Vote_Politician.polid == polid).join(Vote).join(Bill_State).join(topic_bills, Bill_State.bill_id == topic_bills.c.id)
    return topic_votes

def pass_stats(vote_query):
    num_votes = len(vote_query.all())
    vote_translator = {-2:'aqui',-1:'no_vote',0:'no',1:'aye'}
    vote_dict = {'aye':0,'no':0,'aqui':0,'no_vote':0}
    for v in vote_query:
        vote_dict[vote_translator[v.response]] += 1
    return vote_dict


#-----------------------------------------------------------------------------------
#TESTS
#-----------------------------------------------------------------------------------
test_polid = 'P000197'
test_topic_id = 1

def test_politician_topic_bills(polid, topic_id):
    bills = politician_topic_bills(polid, topic_id)
    for b in bills:
        print('testing bill')
        topics = session.query(Topic).filter(Topic.id == topic_id).join(Bill_Topic).join(Bill).filter(Bill.id == b.id)
        if not topics.all():
            print('topic not found in bill, TEST FAILED')
        else:
            print('topics found')
            print(topics.all())

def test_politician_topic_votes(polid, topic_id):
    pol_votes = politician_topic_votes(polid, topic_id)
    failed = False
    for v in pol_votes:
        if v.polid != polid:
            failed = True
            print('incorrect polid!!')
        topics = session.query(Topic).filter(Topic.id == topic_id).join(Bill_Topic).join(Bill).join(Bill_State).join(Vote).join(Vote_Politician).filter(Vote_Politician.id == v.id)
        if not topics.all():
            failed = True
            print('did not find topic in associated vote')
    if failed:
        print('Failed test')


#politician_bills(test_polid)
pol_topic_bills = politician_topic_bills(test_polid, test_topic_id)
test_politician_topic_bills(test_polid, test_topic_id)
#q = politician_topic_votes(test_polid, test_topic_id)
#test_politician_topic_votes(test_polid, test_topic_id)

#pass_stats(q)

polids = session.query(Politician)
topics = session.query(Topic)

for pol in polids:
    pol_name = pol.first_name + " " + pol.last_name
    for t in topics:
        topic_name = t.name

        q = politician_topic_votes(pol.id, t.id)
        print(f'Info on: {pol_name}, {topic_name}')

        if not q.all():
            continue
        print(pass_stats(q))




