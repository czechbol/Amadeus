from sqlalchemy import Column, Integer, BigInteger, DateTime
from repository.database import database


class UserChannel(database.base):
    __tablename__ = "user_channels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(BigInteger)
    user_id = Column(BigInteger)
    count = Column(BigInteger, default=1)
    last_message_at = Column(DateTime)
    guild_id = Column(BigInteger)
