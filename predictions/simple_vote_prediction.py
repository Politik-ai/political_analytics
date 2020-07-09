import sys, os
sys.path.append('../')
sys.path.append('../../data_collection/database_filler')
from framework import *
import pandas as pd

#!/usr/bin/env python3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys, os

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
#

polid = 1

session = Session()
predictive_data = session.query(
    Bill_State, Bill_Topic, Topic, Sponsorship, Vote_Politician
).join(
    Bill, Bill.id == Bill_State.bill_id
).join(
    Vote, Vote.bill_state_id == Bill_State.id
).join(
    Vote_Politician, Vote_Politician.vote_id == Vote.id
).filter(
        Vote_Politician.polid == polid
).join(
    Sponsorship, Sponsorship.bill_id == Bill.id
).join(
    Bill_Topic, Bill_Topic.bill_id == Bill.id
).join(
    Topic, Topic.id == Bill_Topic.topic_id
).yield_per(10000).limit(10000)


i = 0
print('Data_frame data:')
for data in predictive_data:
    print(data)
    print(i)
    i+=1

pd.set_option('display.max_columns', None)
df = pd.read_sql(predictive_data.statement, session.bind)

print(df.head())

