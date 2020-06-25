
from init_db import *
from framework import *
from sqlalchemy import join
from bill_status import *
session = Session()


#BASIC QUERIES -----------------------------------------------------
#Get all bills that were voted upon by a given politician
def politician_bills(polid):
    bill_query = session.query(Bill).join(Bill_State).join(Vote).join(Vote_Politician).filter(Vote_Politician.polid == polid)
    return bill_query

#Return all bills of a given Topic ID
def topic_bills(topic_id):
    return session.query(Bill).join(Bill_Topic).join(Topic).filter(Topic.id == topic_id)

#Given polid, return all votes by that politician on a certain topic
def politician_topic_bills(polid, topic_id):
    pol_bills = politician_bills(polid)
    topic_bills = topic_bills(topic_id)
    pol_topic_bills = pol_bills.union(topic_bills)
    #topic_bills = session.query(Bill).join(pol_bills, Bill.id == pol_bills.c.id).join(Bill_Topic).join(topic_bills, Topic.id == topic_bills.c.id)
    return pol_topic_bills

#return all bill of a given party
def party_sponsor_bills(party):
    party_bills = session.query(Bill).join(Sponsorship).join(Politician).filter(Politician.party == party)
    return party_bills

#Return all bills sponsored by a given politician
def pol_sponsored_bills(polid):
    return session.query(Bill).join(Sponsorship).filter(Sponsorship.polid == polid)

#Returns bills between given dates
def bills_bw_dates(before_date, after_date):
    return session.query(Bill).join(Bill_State).filter(Bill_State.intro_date.between(before_date,after_date))

#Returns politicians that represent a given state
def politician_from_state(state):
    return session.query(Politician).join(Politician_Term).filter(Politician_Term.state == state)
#Returns politicians that represent a given district
def politician_from_state(district):
    return session.query(Politician).join(Politician_Term).filter(Politician_Term.district == district)

#Given query of Bills, what are all of the votes associated?
def votes_from_bills(bill_query):
    bill_subquery = bill_query.subquery()
    votes = session.query(Vote).join(bill_subquery, Bill.id == bill_subquery.id)
    return votes

#Get all sponsors for a given list of bills (bill_query)
def get_sponsors_from_bills(bill_query):
    bill_subquery = bill_query.subquery()
    sponsors = session.query(Politician).join(Sponsorship).join(bill_subquery, Bill.id == bill_subquery.id)
    return sponsors

#Given a party, return all politicians that have been a member of that party
def party_politicians(party):
    return session.query(Politician).join(Politician_Term).filter(Politician_Term.party == party)

#Return topics that given bills contain
def topics_from_bills(bill_query):
    return session.query(Topic).join(Bill_Topic).join(bill_query.subquery, bill_query.id == Bill_Topic.bill_id)


#BASIC GETS --------------------------------------------------------
def get_all_politician():
    return session.query(Politician.id).all()
def get_all_topics():
    return session.query(Topic.id).all()
#Get a list of all parties represented in the Politician_Term table
def get_all_parties():
    return session.query(Politician_Term.party).distinct()
#Get all states represented by Politician_Terms
def get_all_states():
    return session.query(Politician_Term.state).distinct()
#Get all districts represented by Politician_Terms
def get_all_districts():
    return session.query(Politician_Term.district).distinct()

#COMBINATION QUERIES -----------------------------------------------
#Given a politician and Topic, return the set of votes that the politician voted on with that Bill topic. 
def politician_topic_votes(polid, topic_id):
    topic_bills = politician_topic_bills(polid, topic_id).subquery()
    topic_votes = session.query(Vote_Politician).filter(Vote_Politician.polid == polid).join(Vote).join(Bill_State).join(topic_bills, Bill_State.bill_id == topic_bills.c.id)
    return topic_votes


#GET RESULTS--------------------------------------------------------------------------

#Given Pol_Vote query, return formatted dict showing results of those votes.
def pass_stats(vote_query):
    num_votes = len(vote_query.all())
    vote_translator = {-2:'aqui',-1:'no_vote',0:'no',1:'aye'}
    vote_dict = {'aye':0,'no':0,'aqui':0,'no_vote':0}
    for v in vote_query:
        vote_dict[vote_translator[v.response]] += 1
    return vote_dict

#Given Vote query, get formatted dict of the results of that vote
def vote_result(vote):
    pol_votes = session.query(Vote_Politician).join(vote.subquery(), vote.id == Vote_Politician.vote_id)
    return pass_stats(pol_votes)

def bill_query_result_summary(bills):
    votes = votes_from_bills(bills)
    results = {}
    for v in votes:
        results.update(pass_stats(v))
    return results






#COMPARING RESULTS-----------------------------------------------------------------------

#Given list of bill queries and specifiers, return dict of specifier/bill summaries for comparision
def compare_bill_stats(bill_queries, specifiers):
    total_results = {}
    by_queries = {}
    for bq, s in zip(bill_queries, specifiers):
        bq_result = bill_query_result_summary(bq)
        total_results.update(bq_result)
        by_queries[s] = bq_result
    by_queries['total'] = total_results
    return by_queries



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




