from init_db import *
from framework import *
import sys, os
from political_queries import *
import util 
import pandas as pd
from sqlalchemy import distinct, and_
from multiprocessing_base import thread_worker, ThreadPool
sys.path.append(os.path.abspath('../data_collection/database_filler'))
from base import get_session




db_location = sys.argv[1]

session = get_session(db_location)


topic_priorities = session.query(Topic.name, Topic.id, func.count(Bill_Topic.topic_id).label('bill_count'))\
        .join(Bill_Topic)\
            .group_by(Topic.id).all()

print(topic_priorities)

topic_priorities.sort(key = lambda x: x[2])

print(topic_priorities)

for s in topic_priorities:
    print(s)
