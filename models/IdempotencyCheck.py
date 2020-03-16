from main import db
from sqlalchemy import Column, String, Integer


class Idempotency(db.Model):
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
