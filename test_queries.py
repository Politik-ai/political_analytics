#!/usr/bin/env python3
from political_queries import *
import unittest
from datetime import date 


class TestQueries(unittest.TestCase):

    def test_politician_bills(self):
        polid = 5
        pols = get_all_politicians(session)
        for pol in pols:
            bills = politician_bills(session, pol.id)
            #print(len(bills.all()))
        for b in bills:
            #print(b.id)
            continue


    def test_politician_topic_bills(self):
        polid = 2
        topic_id = 1
        bills = politician_topic_bills(session, polid, topic_id)
        for b in bills:
            topics = session.query(Topic).filter(Topic.id == topic_id).join(Bill_Topic).join(Bill).filter(Bill.id == b.id)
            self.assertFalse(not topics.all())

    def test_politician_topic_votes(self):
        polid = 2
        topic_id = 1
        pol_votes = politician_topic_votes(session, polid, topic_id)
        failed = False
        for v in pol_votes:
            self.assertEqual(polid, v.polid)
            topics = session.query(Topic).filter(Topic.id == topic_id).join(Bill_Topic).join(Bill).join(Bill_State).join(Vote).join(Vote_Politician).filter(Vote_Politician.id == v.id)
            self.assertFalse(not topics.all())

    def test_pol_sponsored_bills(self):
        polid = 2
        bills = pol_sponsored_bills(session, polid)
        for b in bills:
            sponsors = session.query(Politician).join(Sponsorship).filter(Sponsorship.bill_id == b.id).all()
            sponsor_ids = [s.id for s in sponsors]
            self.assertTrue(polid in sponsor_ids)

    def test_bill_states_bw_dates(self):
        before_date = date(2013,6,6)
        after_date = date(2013, 10,6)
        bills = bill_states_bw_dates(session, before_date,after_date)
        for b in bills:
            self.assertTrue(before_date <= b.intro_date and after_date >= b.intro_date)

    def test_politician_from_state(self):
        state = 'CO'
        politicians = politicians_from_state(session, state)

        for p in politicians:
            pol_states = session.query(Politician_Term).filter(Politician_Term.polid == p.id)
            for ps in pol_states:
                self.assertEqual(ps.state, state)

    def test_politician_from_district(self):
        district = 13
        politicians = politicians_from_district(session, district)
        for p in politicians:
            found = False
            pol_district = session.query(Politician_Term).filter(Politician_Term.polid == p.id)
            for ps in pol_district:
                if ps.district == district:
                    found = True
        self.assertTrue(found)


    def test_votes_from_bills(self):
        #get bills sponsored by given politicians
        polid = 1
        bills = pol_sponsored_bills(session, polid)
        bill_ids = [b.id for b in bills.all()]
        votes = votes_from_bills(session, bills)

        self.assertTrue(not not votes)
        if votes.all() is None:
            print('ending early')
            return

        for v in votes:
            bill_id = session.query(Bill.id).join(Bill_State).filter(Bill_State.id == v.bill_state_id).first()[0]
            self.assertTrue(bill_id in bill_ids)
            #NOTE: FOR INCREASED ROBUSTNESS, also check that each bill is accounted for in votes

    def test_party_politician(self):
        test_party = "Democrat"
        pols = party_politicians(session, test_party)
        for p in pols:
            terms = session.query(Politician_Term).filter(Politician_Term.polid == p.id)
            was_party = False
            for t in terms:
                was_party = was_party or (t.party == test_party)
            self.assertTrue(was_party)

    #How should periods be tested? Realistically, we need a proto-database for testing...
    def test_get_leadership_periods(self):
        polid = 1
        periods = get_leadership_periods(session, polid)
        #for p in periods:

    def test_topics_from_bills(self):
        topics_set = {1,2}

        topic1_bills = topic_bills(session, 1)
        topic2_bills = topic_bills(session, 2)
        t_bills = topic1_bills.union(topic2_bills)
        topics = topics_from_bills(session, t_bills)

        found_topics = set()
        for t in topics:
            found_topics.add(t.id)
        self.assertTrue(topics_set.issubset(found_topics))        




if __name__ == '__main__':
    session = Session()
    unittest.main()

