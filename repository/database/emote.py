from sqlalchemy import Column, Integer, String, BigInteger, Boolean
from repository.database import database


class Emote(database.base):
    __tablename__ = "emote_table"

    emote_id = Column(BigInteger, primary_key=True)
    guild_id = Column(BigInteger)
    name = Column(String)
    animated = Column(Boolean)
    count = Column(Integer, default=0)
    original_name = Column(String)

    def __repr__(self):
        return f'<Emote id="{self.emote_id}" guild="{self.guild_id}" name="{self.name}" animated="{self.animated}" count="{self.count}" original_name="{self.original_name}">'
