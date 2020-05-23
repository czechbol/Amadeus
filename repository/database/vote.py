from sqlalchemy import Column, BigInteger, DateTime
from repository.database import database

class Vote(database.base):
    __tablename__ = 'votes'

    message_id    = Column(BigInteger, primary_key=True)
    channel_id    = Column(BigInteger)
    edit_id       = Column(BigInteger)
    date          = Column(DateTime)
