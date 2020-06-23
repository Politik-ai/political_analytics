from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
sys.path.append('/home/jmaguila/Documents/ProjectAI/data_collection/database_filler')
import framework


engine = create_engine('sqlite:////home/jmaguila/Documents/ProjectAI//data_collection/political_db.db', echo=True)
Session = sessionmaker(bind=engine)