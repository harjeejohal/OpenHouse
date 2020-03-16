from main import db
from sqlalchemy import Column, String, Integer, DateTime


class LogFailure(db.Model):
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
