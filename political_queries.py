
from init_db import *
from framework import *
from sqlalchemy import join
from bill_status import *
#session = Session()


#BASIC QUERIES -----------------------------------------------------
#Get all bills that were voted upon by a given politician
def politician_bills(session, polid):
    result = session.query(Bill).join(Bill_State).join(Vote).join(Vote_Politician).filter(Vote_Politician.polid == polid)
    return result   

def get_all_bills_voted_on(session):
    return session.query(Bill_State).join(Vote)

#Return all bills that contain given Topic ID
def topic_bills(session, topic_id, bill_query = None):
    if bill_query:
        bill_sub = bill_query.subquery()
        b_id, bill_code, status, originating_body = tuple(bill_sub.c)
        return session.query(Bill).join(bill_sub, Bill.id == b_id).join(Bill_Topic).join(Topic).filter(Topic.id == topic_id)
    return session.query(Bill).join(Bill_Topic).join(Topic).filter(Topic.id == topic_id)

#return all bill of a given party
def party_primary_sponsor_bills(session, party):
    party_bills = session.query(Bill).join(Bill_State).join(Sponsorship).join(Politician).join(Politician_Term)\
        .filter(Politician_Term.party == party, \
        Politician_Term.start_date <= Bill_State.intro_date, \
        Politician_Term.end_date >= Bill_State.intro_date, \
        Sponsorship.sponsor_type == 'primary')
    return party_bills

#Return all bills sponsored by a given politician
def pol_sponsored_bills(session, polid):
    return session.query(Bill).join(Sponsorship).filter(Sponsorship.polid == polid)

#Returns bills between given dates
def bill_states_bw_dates(session, before_date, after_date):
    return session.query(Bill_State).filter(Bill_State.intro_date.between(before_date,after_date))

#Returns politicians that represent a given state
def politicians_from_state(session, state):
    return session.query(Politician).join(Politician_Term).filter(Politician_Term.state == state)

#Returns politicians that represent a given district
def politicians_from_district(session, district):
    return session.query(Politician).join(Politician_Term).filter(Politician_Term.district == district)

#Given query of Bills, what are all of the votes associated?
def votes_from_bills(session, bill_query):
    bill_subquery = bill_query.subquery()
    b_id, bill_code, status, originating_body = tuple(bill_subquery.c)

    votes = session.query(Vote).join(Bill_State).join(bill_subquery, Bill_State.bill_id == b_id)
    return votes

def pol_votes_from_votes(session, vote_query, polid):
    vote_sub = vote_query.subquery()
    v_id, bs_id, vote_date = vote_sub.c
    return session.query(Vote_Politician).join(Vote).join(vote_sub, v_id == Vote.id).filter(Vote_Politician.polid == polid)

#Filter politicians by ones that were active on given date
def filter_pols_by_congress(session, pol_query, filter_date):
    pol_sub = pol_query.subquery()
    return session.query(Politician).join(pol_sub, pol_sub.c.id == Politician.id).join(Politician_Term).filter(Politician_Term.start_date <= filter_date, Politician_Term.end_date >= filter_date)
    

#TODO: TEST
#Get all sponsors for a given list of bills (bill_query)
def get_sponsors_from_bills(session, bill_query):
    bill_subquery = bill_query.subquery()
    sponsors = session.query(Politician).join(Sponsorship).join(bill_subquery, Bill.id == bill_subquery.id)
    return sponsors

#Given a party, return all politicians that have been a member of that party
def party_politicians(session, party):
    return session.query(Politician).join(Politician_Term).filter(Politician_Term.party == party)

def was_leader(session, date, polid):
    role =  session.query(Leadership_Role).join(Politician).filter(Politician.id == polid).join(Politician_Term)\
    .filter(Politician_Term.start_date <= date, Politician_Term.end_date >= date)
    return not not role

#Returns a list of periods that a politician has been a leader
def get_leadership_periods(session, polid):
    leadership_roles = session.query(Leadership_Role).join(Politician).filter(Politician.id == polid)
    if not leadership_roles:
        raise Exception('Given politician was not a leader.')
    periods = []
    for role in leadership_roles:
        periods.append(tuple(role.start_date,role.end_date))
    return periods


#TODO: TEST
#Get all leaders of given party
def party_leaders(session, party):
    leaders = get_leadership(session)
    party_members = party_politicians(party, session)
    return party_members.intersect(leaders)


#Return topics that given bills contain.
def topics_from_bills(session, bill_query):
    b_sub = bill_query.subquery()
    b_id, bill_code, status, originating_body = tuple(b_sub.c)
    results =  session.query(Topic).join(Bill_Topic).join(b_sub, b_id == Bill_Topic.bill_id)
    return results


#BASIC GETS --------------------------------------------------------

def get_all_politician(session):
    return session.query(Politician.id).all()
def get_all_topics(session):
    return session.query(Topic).all()
#Get a list of all parties represented in the Politician_Term table
def get_all_parties(session):
    return session.query(Politician_Term.party).distinct()
#Get all states represented by Politician_Terms
def get_all_states(session):
    return session.query(Politician_Term.state).distinct()
#Get all districts represented by Politician_Terms
def get_all_districts(session):
    return session.query(Politician_Term.district).distinct()
#Get all politicians with leadership roles
def get_leadership(session):
    return session.query(Politician).join(Leadership_Role)
#Get all active politician terms on a given date
def get_politician_terms_on_day(date, session):
    return session.query(Politician_Term).filter(Politician_Term.start_date <= date, Politician_Term.end_date >= date)

#COMBINATION QUERIES -----------------------------------------------
#Given polid, return all bills voted on by a politician on a certain topic
def politician_topic_bills(session, polid, topic_id):
    pol_bills = politician_bills(session, polid)
    top_bills = topic_bills(session, topic_id)
    pol_topic_bills = pol_bills.intersect(top_bills)
    return pol_topic_bills

#Given a politician and Topic, return the set of votes that the politician voted on with that Bill topic. 
def politician_topic_votes(session, polid, topic_id):
    pol_topic_bills = politician_topic_bills(session, polid, topic_id).subquery()
    
    b_id, bill_code, status, originating_body = tuple(pol_topic_bills.c)

    topic_votes = session.query(Vote_Politician).filter(Vote_Politician.polid == polid) \
        .join(Vote).join(Bill_State).join(Bill) \
        .join(pol_topic_bills, Bill.id == b_id)
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
def vote_result(vote, session):
    pol_votes = session.query(Vote_Politician).join(vote.subquery(), vote.id == Vote_Politician.vote_id)
    return pass_stats(pol_votes)

def votes_summary(votes):
    results = {}
    for v in votes:
        results.update(pass_stats(v))
    return results

#Returns single summary dict of given bills
def bill_query_result_summary(bills, session):
    votes = votes_from_bills(bills)
    return votes_summary(votes)

#Given politician, create by-topic summary of votes
def pol_topic_stats(polid, session):
    stats = {}
    for t in get_all_topics(session):
        topic_votes = politician_topic_votes(polid, t.id, session)
        stats[t.name] = votes_summary(topic_votes)
    return stats
            

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

