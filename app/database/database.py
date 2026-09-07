import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATA_DIR = os.path.join(BASE_DIR, 'data')

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

DB_PATH = os.path.join(DATA_DIR, 'optischedule.db')
DATABASE_URL = f"sqlite:///{DB_PATH}"

from sqlalchemy.pool import NullPool
from sqlalchemy import event
from contextlib import contextmanager

engine = create_engine(
    DATABASE_URL, 
    echo=False, 
    poolclass=NullPool, 
    connect_args={"check_same_thread": False, "timeout": 30.0}
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")
    finally:
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    Base.metadata.create_all(bind=engine)

@contextmanager
def get_db_session():
    """Context manager for transactional database operations."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_db():
    """Generator yielding a session, with cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
