from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
sys.path.append('../data_collection/database_filler')
import framework


engine = create_engine('sqlite:///../data_collection/political_db.db', echo=False)
Session = sessionmaker(bind=engine)