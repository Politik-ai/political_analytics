#!/usr/bin/env python3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
sys.path.append('../data_collection/database_filler')


engine = create_engine('sqlite:///../data_collection/political_db.db', echo=False)
Session = sessionmaker(bind=engine)