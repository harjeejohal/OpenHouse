from sqlalchemy import Column, String, DateTime, JSON, Integer
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

db = sqlalchemy.create_engine(
    # Equivalent URL:
    # postgres+pg8000://<db_user>:<db_pass>@/<db_name>?unix_sock=/cloudsql/<cloud_sql_instance_name>/.s.PGSQL.5432
    sqlalchemy.engine.url.URL(
        drivername='postgres+pg8000',
        username='postgres',
        password='Openhouse1!',
        database='openhouse-logs',
        query={
            'unix_sock': '/cloudsql/{}/.s.PGSQL.5432'.format(
                'openhouse-project:us-central1:openhouse-db')
        }
    )
)

Base = declarative_base()
db_session = Session(bind=db, autocommit=False, autoflush=False)


class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True)
    sessionId = Column('session_id', String())
    time = Column('time', DateTime)
    userId = Column('user_id', String())
    type = Column('type', String())
    properties = Column('properties', JSON)

    def __init__(self, user_id, session_id, time, action_type, properties):
        self.sessionId = session_id
        self.userId = user_id
        self.time = time
        self.type = action_type
        self.properties = properties

    def __repr__(self):
        return 'id ({}, {}, {})'.format(self.sessionId, self.userId, self.time)

    def serialize(self):
        return {
            'userId': self.userId,
            'sessionId': self.sessionId,
            'time': self.time,
            'type': self.type,
            'properties': self.properties
        }


class LogFailure(Base):
    __tablename__ = "log_failures"

    id = Column(Integer, primary_key=True)
    log_timestamp = Column('log_timestamp', DateTime)
    error_message = Column('error_message', String())
    error_count = Column('error_count', Integer)
    error_type = Column('error_type', String())

    def __init__(self, log_timestamp, error_message, error_count, error_type):
        self.log_timestamp = log_timestamp
        self.error_message = error_message
        self.error_count = error_count
        self.error_type = error_type

    def __repr__(self):
        return 'id ({}, {}, {}, {})'.format(self.log_timestamp, self.error_message, self.error_count, self.error_type)

    def serialize(self):
        return {
            'log_timestamp': self.log_timestamp,
            'error_message': self.error_message,
            'error_count': self.error_count,
            'error_type': self.error_type
        }


class Idempotency(Base):
    __tablename__ = "idempotency"

    key = Column('key', String(), primary_key=True)

    def __init__(self, key):
        self.key = key

    def __repr__(self):
        return 'id ({})'.format(self.key)

    def serialize(self):
        return {
            'key': self.key
        }
