from contextlib import contextmanager
from multiprocessing import Pool as ThreadPool
from init_db import *

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

def thread_worker(f, args):
    # We're using the session context here.
    with session_scope() as session:
        return f(session, *args)
