from datetime import datetime

from repository.base_repository import BaseRepository
from repository.database import session
from repository.database.tempverify import Tempverify


class TempverifyRepository(BaseRepository):
    # unknown - pending - verified - kicked - banned
    @classmethod
    def add(self, guild_id: int, user_id: int, end_time: datetime):
        """Adds tempverify to the database"""
        tempverify = session.query(Tempverify).filter_by(user_id=user_id).one_or_none()

        if not tempverify:
            added = Tempverify(
                guild_id=guild_id,
                user_id=user_id,
                end_time=end_time,
            )
            session.add(added)
            session.commit()
        else:
            added = None
        return added

    @classmethod
    def delete(self, idx: int):
        """Removes unverify from the database"""
        unverify = session.query(Tempverify).filter_by(idx=idx).one_or_none()
        if not unverify:
            removed = None
        else:
            session.delete(unverify)
            removed = unverify

        session.commit()

        return removed

    @classmethod
    def get_all(cls):
        """Retrieves waiting unverifies."""
        return session.query(Tempverify).order_by(Tempverify.end_time.asc()).all()
