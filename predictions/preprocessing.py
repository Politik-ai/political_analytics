#!/usr/bin/env python3
import sys, os, yaml
sys.path.append('../')
sys.path.append('../../data_collection/database_filler')
from framework import *
import pandas as pd
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from political_queries import *
sys.path.append(os.path.abspath('../../data_collection/database_filler'))
engine = create_engine('sqlite:///' + os.path.abspath('../../data_collection/political_db.db'), echo=False)
Session = sessionmaker(bind=engine)

#What columns do we want
"""
Each bill_state_vote basically:

Add boolean column for each topic?
Add boolean column for each sponsor? (add sponsor type?)
#Dummy variables

The 'y' variable is vote response. (trying to predict that)

Bill_State, Vote, Vote_Politician, Bill_Topic, Topic, Sponsorship
"""
from datetime import date

session = Session()
predictive_data = session.query(
    Bill
).yield_per(10000)

df = pd.read_sql(predictive_data.statement, session.bind)
print('Got dataframe')

sponsor_id_dict = {}
topic_dict = {}
i = 0
num_bills = len(df['id'])
for bill_id in df['id']:
    i += 1
    print(f'getting {i}/{num_bills} topic/sponsors')
    s = get_sponsor_from_bill_id(session, bill_id)
    sponsor_id_dict[bill_id] = set([s.id for s in s.all()])
    t = get_topics_from_bill_id(session, bill_id)
    topic_dict[bill_id] = set([t.id for t in t.all()])


with open("sponsor_id.yaml", "w") as sponsor_id:
    yaml.dump(sponsor_id_dict, sponsor_id)
with open("topic.yaml", "w") as topic:
    yaml.dump(topic_dict, topic)
