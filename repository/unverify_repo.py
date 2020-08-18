from datetime import datetime

from repository.base_repository import BaseRepository
from repository.database import session
from repository.database.unverify import Unverify


class UnverifyRepository(BaseRepository):
    # unknown - pending - verified - kicked - banned
    @classmethod
    def add(
        self,
        guild_id: int,
        user_id: int,
        start_time: datetime,
        end_time: datetime,
        roles_to_return: list,
        channel_overrides: list,
        reason: str,
    ):
        """Adds unverify to the database"""
        unverify = session.query(Unverify).filter_by(user_id=user_id).one_or_none()

        if not unverify:
            added = Unverify(
                guild_id=guild_id,
                user_id=user_id,
                start_time=start_time,
                end_time=end_time,
                roles_to_return=roles_to_return,
                channel_overrides=channel_overrides,
                reason=reason,
            )
            session.add(added)
            session.commit()
        else:
            added = None
        return added

    def set_finished(self, idx: int):
        """Set reminder as finished"""
        unverify = session.query(Unverify).filter_by(idx=idx).one_or_none()

        if not unverify:
            return None

        else:
            unverify.status = "finished"
            session.commit()
        return unverify

    @classmethod
    def delete(self, idx: int):
        """Removes unverify from the database"""
        unverify = session.query(Unverify).filter_by(idx=idx).one_or_none()
        if not unverify:
            removed = None
        else:
            session.delete(unverify)
            removed = unverify

        session.commit()

        return removed

    @classmethod
    def get_waiting(cls):
        """Retrieves waiting unverifies."""
        return session.query(Unverify).filter_by(status="waiting").order_by(Unverify.end_time.asc()).all()

    @classmethod
    def get_finished(cls):
        """Retrieves waiting unverifies."""
        return session.query(Unverify).filter_by(status="finished").order_by(Unverify.end_time.asc()).all()

    @classmethod
    def get_ordered(cls):
        """Retrieves the whole table."""
        return session.query(Unverify).order_by(Unverify.end_time.asc()).all()

    @classmethod
    def get_user(cls, user_id: int):
        """Retrieves table, filtered by user id."""
        return session.query(Unverify).filter_by(user_id=user_id).all()

    @classmethod
    def get_idx(cls, idx: int):
        """Retrieves table, filtered by idx."""
        return session.query(Unverify).filter_by(idx=idx).order_by(Unverify.end_time.asc()).all()
