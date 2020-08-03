from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from repository.database import database


class Reminder(database.base):
    __tablename__ = "remindme_table"

    idx = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger)
    reminder_user_id = Column(BigInteger)
    permalink = Column(String)
    message = Column(String)
    origin_date = Column(DateTime)
    new_date = Column(DateTime)
    status = Column(String, default="waiting")
