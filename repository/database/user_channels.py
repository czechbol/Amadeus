from sqlalchemy import Column, Integer, BigInteger, Boolean, DateTime
from repository.database import database


class UserChannel(database.base):
    __tablename__ = "user_channels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger)
    channel_id = Column(BigInteger)
    user_id = Column(BigInteger)
    is_webhook = Column(Boolean)
    count = Column(BigInteger, default=1)
    last_msg_at = Column(DateTime)
