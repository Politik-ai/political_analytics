
from init_db import *
from framework import *
from sqlalchemy import join
from bill_status import *
from sqlalchemy import func
import util

#BASIC QUERIES -----------------------------------------------------
#Get all bills that were voted upon by a given politician
def politician_bills(session, politician_id):
    result = session.query(Bill).join(Bill_State).join(Vote).join(Vote_Politician).filter(Vote_Politician.politician_id == politician_id)
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
def party_primary_sponsor_bills(session, party, bill_query=None):

    party_bills = session.query(Bill).join(Bill_State).join(Sponsorship).join(Politician).join(Politician_Term)\
        .filter(Politician_Term.party == party, \
        Politician_Term.start_date <= Bill_State.intro_date, \
        Politician_Term.end_date >= Bill_State.intro_date, \
        Sponsorship.sponsor_type == 'primary')



    if bill_query:

        bill_sub = bill_query.with_entities(Bill.id).subquery()
        party_bills = party_bills.filter(Bill.id.in_(bill_sub))
        
    return party_bills


def get_resolutions_from_bills(session, bill_query=None):

    resolution_indicators = ['']

    resolutions = session.query(Bill).filter()


#Return all bills sponsored by a given politician
def pol_sponsored_bills(session, politician_id):
    return session.query(Bill).join(Sponsorship).filter(Sponsorship.politician_id == politician_id)

#Return all bills primarily sponsored by a given politician
def pol_primary_sponsored_bills(session, polid):
    return session.query(Bill).join(Sponsorship).filter(Sponsorship.polid == polid, Sponsorship.sponsor_type == 'primary')

#Returns bill states active between given dates
def bill_states_bw_dates(session, before_date, after_date, bill_state_query = None):
    if not bill_state_query:
        return session.query(Bill_State).filter(Bill_State.intro_date.between(before_date,after_date))
    else:
        bill_state_subquery = bill_state_query.subquery()
        b_id, bill_code, status, originating_body = tuple(bill_state_subquery.c)
        return session.query(Bill_State).join(bill_state_subquery, Bill_State.id == b_id).filter(Bill_State.intro_date.between(before_date,after_date))

#Returns bills active between given dates
def bill_bw_dates(session, before_date, after_date, bill_query = None):
    if not bill_query:
        return session.query(Bill).join(Bill_State).filter(Bill_State.intro_date.between(before_date,after_date))
    else:
        #print(f"dates before: {before_date}, after: {after_date}")
        bill_subquery = bill_query.with_entities(Bill.id).subquery()


        range_query =  session.query(Bill)\
                .join(Bill_State)\
                    .filter(Bill_State.intro_date.between(before_date,after_date))
                        #.filter(Bill.id.in_(bill_subquery))

        bill_ids = [bill.id for bill in bill_query if bill is not None]
        range_ids = [bill.id for bill in range_query if bill is not None]
        intersect_id = [value for value in range_ids if value in bill_ids]
        #print('intersect of ids:')
        #print(intersect_id)
        #print(type(bill_query.first().id))
        #print(type(range_query.first().id))

        return range_query.intersect(bill_query)

#Returns the date ranges of the current db
def get_bill_state_date_ranges(session):

    qry = session.query(func.min(Bill_State.intro_date).label("min_date"), func.max(Bill_State.intro_date).label("max_date"))
    res = qry.one()
    return [res.min_date, res.max_date]

#Returns politicians that represent a given state
def politicians_from_state(session, state):
    return session.query(Politician).join(Politician_Term).filter(Politician_Term.state == state)

#Returns politicians that represent a given district
def politicians_from_district(session, district):
    return session.query(Politician).join(Politician_Term).filter(Politician_Term.district == district)

#Given query of Bills, what are all of the votes associated?
def votes_from_bills(session, bill_query):
    bill_subquery = bill_query.with_entities(Bill.id).subquery()
    #b_id, bill_code, status, originating_body = tuple(bill_subquery.c)
    votes = session.query(Vote).join(Bill).filter(Bill.id.in_(bill_subquery))
    return votes

#Get pol_votes associated with given vote_query for a given polid
def pol_votes_from_votes(session, vote_query, polid):
    vote_sub = vote_query.subquery()
    v_id, bs_id, vote_date = vote_sub.c
    return session.query(Vote_Politician).join(Vote).join(vote_sub, v_id == Vote.id).filter(Vote_Politician.polid == polid)

#Get all pol_votes associated with given vote_query
def vote_pols_from_votes(session, vote_query):

    vote_sub = vote_query.with_entities(Vote.id).subquery()

    return session.query(Vote_Politician).join(Vote).filter(Vote.id.in_(vote_sub))

def votes_between_dates(session, range, vote_query = None):
    if not vote_query:
        return session.query(Vote).filter(Vote.vote_date.between(*range))
    
    vote_sub = vote_query.with_entities(Vote.id).subquery()
    return session.query(Vote).filter(Vote.vote_date.between(*range)).filter(Vote.id.in_(vote_sub))

#Filter politicians by ones that were active on given date
def filter_pols_by_date(session, pol_query, filter_date):
    pol_sub = pol_query.subquery()
    return session.query(Politician).join(pol_sub, pol_sub.c.id == Politician.id).join(Politician_Term).filter(Politician_Term.start_date <= filter_date, Politician_Term.end_date >= filter_date)

#Returns subset of given pols that were from a given state
def filter_pols_by_state(session, pol_query, state):
    pol_sub = pol_query.subquery()
    return session.query(Politician).join(pol_sub, pol_sub.c.id == Politician.id).join(Politician_Term).filter(Politician_Term.state == state)
    
#Return subset of given bills that contain given topic
def filter_bills_by_topic(session, bill_query, topic_id):
    bill_subquery = bill_query.subquery()
    b_id, bill_code, status, originating_body = tuple(bill_subquery.c)
    return session.query(Bill).join(bill_subquery, Bill.id == b_id).join(Bill_Topic).filter(Bill_Topic.topic_id == topic_id)

#Given vote_query, return pol_votes that are from a given party
def pol_votes_from_party(session, vote_query, party):
    vote_sub = vote_query.subquery()
    v_id, bs_id, vote_date = vote_sub.c
    return session.query(Vote_Politician).join(Vote).join(vote_sub, v_id == Vote.id)\
        .join(Bill_State).join(Politician).join(Politician_Term)\
        .filter(Politician_Term.party == party, \
        Politician_Term.start_date <= Bill_State.intro_date, \
        Politician_Term.end_date >= Bill_State.intro_date)


#TODO: TEST
#Get all sponsors for a given list of bills (bill_query)
def get_sponsors_from_bills(session, bill_query):
    
    bill_ids_sub = bill_query.with_entities(Bill.id).subquery()
    sponsors = session.query(Sponsorship)\
        .join(Bill)\
            .filter(Bill.id.in_(bill_ids_sub))

    return sponsors

#Get all sponsors for a given list of bills (bill_query)
"""
def get_sponsors_from_billstates(session, bill_state_query):
    #bill_state_subquery = bill_state_query.subquery()
    #print(bill_state_subquery.c)
    #bill_id = bill_state_subquery.c[1]
    #b_id, bill_code, status, originating_body = tuple(bill_state_subquery.c)
    bs_sub = bill_state_query.subquery()

    bs_ids = Sponsorship.query.join(Bill).join(Bill)

    print(bs_ids)
    print('-----')
    #s = session.query(Sponsorship).join(Bill).filter(Bill.id.in_(bs_ids))
    s = bs_ids
    #sponsors = bill_state_query.join(Bill).join(Sponsorship)
    return s
    """

def party_only_sponsorships(session, sponsor_query, party, range):

    party_pols = session.query(Politician_Term).\
    filter(Politician_Term.start_date >= range[0],\
     Politician_Term.end_date >= range[1]).\
     filter(Politician_Term.party == party).with_entities(Politician_Term.politician_id)
    
    q = sponsor_query.join(Politician).filter(Politician.id.in_(party_pols.subquery()))

    #print(q)
    return q
    #sponsor_subquery = sponsor_query.subquery()
    #sponsors = session.query(Sponsorship).filter(sponsor_subquery).join(Politician).join(Politician_Term).filter(Politician_Term.party == party)
    #print(sponsors.first())
    #return sponsors

def get_sponsor_from_bill_id(session, bill_id):
    return session.query(Politician).join(Sponsorship).filter(Sponsorship.bill_id == bill_id)

def get_primary_sponsor_from_bill_id(session, bill_id):
    return session.query(Politician).join(Sponsorship).filter(Sponsorship.bill_id == bill_id, Sponsorship.sponsor_type == 'primary')

def get_topics_from_bill_id(session, bill_id):
    return session.query(Topic).join(Bill_Topic).filter(Bill_Topic.bill_id == bill_id)

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

def count_results(session, query):
    return query.count()

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

def get_all_politicians(session):
    return session.query(Politician.id)
def get_all_topics(session):
    return session.query(Topic).all()
#Get a list of all parties represented in the Politician_Term table
def get_all_parties(session):
    return session.query(Politician_Term.party).distinct()
#Get all states represented by Politician_Terms
def get_all_states(session):
    return [item[0] for item in session.query(Politician_Term.state).distinct()]
#Get all districts represented by Politician_Terms
def get_all_districts(session):
    return session.query(Politician_Term.district).distinct()
#Get all politicians with leadership roles
def get_leadership(session):
    return session.query(Politician).join(Leadership_Role)
#Get all active politician terms on a given date
def get_politician_terms_on_day(session, date):
    return session.query(Politician_Term).filter(Politician_Term.start_date <= date, Politician_Term.end_date >= date)

#COMBINATION QUERIES -----------------------------------------------
#Given polid, return all bills voted on by a politician on a certain topic
def politician_topic_bills(session, polid, topic_id):
    pol_bills = politician_bills(session, polid)
    top_bills = topic_bills(session, topic_id)
    pol_topic_bills = pol_bills.intersect(top_bills)
    return pol_topic_bills

#Given a politician and Topic, return the set of votes that the politician voted on with that Bill topic. 
def politician_topic_votes(session, politician_id, topic_id):
    pol_topic_bills = politician_topic_bills(session, politician_id, topic_id).with_entities(Bill.id)
    
    #b_id, bill_code, status, originating_body = tuple(pol_topic_bills.c)

    topic_votes = session.query(Vote_Politician).filter(Vote_Politician.politician_id == politician_id) \
        .join(Vote).join(Bill).filter(Bill.id.in_(pol_topic_bills.subquery()))
    return topic_votes


#GET RESULTS--------------------------------------------------------------------------

#Given Pol_Vote query, return formatted dict showing results of those votes.
def pass_stats(vote_query):
    #num_votes = len(vote_query.all())
    vote_translator = {-2:'aqui',-1:'no_vote',0:'no',1:'aye'}
    vote_dict = {'aye':0,'no':0,'aqui':0,'no_vote':0}
    i = 0
    for v in vote_query:
        i += 1
        vote_dict[vote_translator[v.response]] += 1
    return vote_dict

#Given Vote query, get formatted dict of the results of that vote
def vote_result(session, vote):
    pol_votes = session.query(Vote_Politician).join(vote.subquery(), vote.id == Vote_Politician.vote_id)
    return pass_stats(pol_votes)

def votes_summary(votes):
    results = {}
    for v in votes:
        new_stats = pass_stats(v)
        results.update(pass_stats(v))
    return results

#Returns single summary dict of given billsget
def bill_query_result_summary(session, bills):
    votes = votes_from_bills(bills)
    return votes_summary(votes)

#Given politician, create by-topic summary of votes
def pol_topic_stats(session, polid):
    stats = {}
    for t in get_all_topics(session):
        topic_votes = politician_topic_votes(polid, t.id, session)
        stats[t.name] = votes_summary(topic_votes)
    return stats

def pass_stats_average(pol_results):
    total_votes = sum(pol_results.values()) - pol_results['no_vote']
    if total_votes == 0:
        return 0
    ratio = round(pol_results['aye']/total_votes ,3)
    return ratio


            

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

