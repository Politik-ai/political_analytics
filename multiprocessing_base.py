from contextlib import contextmanager
from multiprocessing import Pool as ThreadPool
from init_db import *
sys.path.append(os.path.abspath('../data_collection/database_filler'))
from base import get_session

@contextmanager
def session_scope(db):
    """Provide a transactional scope around a series of operations."""
    session = get_session(db)
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

def thread_worker(f, db, args):
    # We're using the session context here.
    with session_scope(db) as session:
        return f(session, db, *args)
