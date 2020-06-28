from political_queries import *
import unittest
from datetime import date 


class TestQueries(unittest.TestCase):


    def test_party_primary_sponsor_bills(self):
        test_party = "Democrat"
        party_bills = party_primary_sponsor_bills(test_party)
        num_bills = len(party_bills.all())
        i = 0
        for pb in party_bills:
            i +=1
            found_pb = False
            sponsor = session.query(Politician_Term).join(Politician).join(Sponsorship).filter(pb.id == Sponsorship.bill_id).first()
            self.assertTrue(sponsor.party == test_party)






if __name__ == '__main__':
    unittest.main()