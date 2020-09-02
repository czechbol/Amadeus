from sqlalchemy import Column, Integer, DateTime, BigInteger
from repository.database import database


class Tempverify(database.base):
    __tablename__ = "tempverify_table"

    idx = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger)
    user_id = Column(BigInteger)
    end_time = Column(DateTime)
