from sqlalchemy import ARRAY, Column, Integer, String, DateTime, BigInteger
from repository.database import database


class Unverify(database.base):
    __tablename__ = "unverify_table"

    idx = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger)
    user_id = Column(BigInteger)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    roles_to_return = Column(ARRAY(BigInteger))
    channels_to_return = Column(ARRAY(BigInteger))
    channels_to_remove = Column(ARRAY(BigInteger))
    reason = Column(String)
    status = Column(String, default="waiting")
    typ = Column(String)
