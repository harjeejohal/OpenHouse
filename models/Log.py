from main import db
from sqlalchemy import Column, String, DateTime, JSON


class Log(db.Model):
    __tablename__ = "logs"

    id = Column(db.Integer, primary_key=True)
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
