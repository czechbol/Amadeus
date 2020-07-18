from datetime import datetime
import sqlalchemy

from repository.base_repository import BaseRepository
from repository.database import session
from repository.database.remind import Reminder


class RemindRepository(BaseRepository):
    # unknown - pending - verified - kicked - banned
    @classmethod
    def add(
        self,
        user_id: int,
        reminder_user_id: str,
        permalink: str,
        message: str,
        origin_date: datetime,
        new_date: datetime,
    ):
        """Adds reminder to the database"""
        reminder = session.query(Reminder).filter_by(permalink=permalink).one_or_none()

        if not reminder:
            added = Reminder(
                user_id=user_id,
                reminder_user_id=reminder_user_id,
                permalink=permalink,
                message=message,
                origin_date=origin_date,
                new_date=new_date,
            )
            session.add(added)

        else:
            if Reminder.user_id == user_id and Reminder.message == message and Reminder.new_date == new_date:
                added = None
            else:
                added = Reminder(
                    user_id=user_id,
                    reminder_user_id=reminder_user_id,
                    permalink=permalink,
                    message=message,
                    origin_date=origin_date,
                    new_date=new_date,
                )
                session.add(added)

        session.commit()
        return added

    @classmethod
    def delete(self, idx: int):
        """Removes reminder from the database"""
        reminder = session.query(Reminder).filter_by(idx=idx).one_or_none()
        if not reminder:
            removed = None
        else:
            session.delete(reminder)
            removed = reminder
        
        session.commit()

        return removed

    @classmethod
    def get_ordered(cls):
        """Retrieves the whole table."""
        return session.query(Reminder).order_by(Reminder.new_date.asc()).all()

    @classmethod
    def get_user(cls, user_id: int):
        """Retrieves table, filtered by user id."""
        return session.query(Reminder).filter_by(user_id=user_id).order_by(Reminder.new_date.asc()).all()

    @classmethod
    def get_permalink(cls, permalink):
        """Retrieves table, filtered by permalink."""
        return session.query(Reminder).filter_by(permalink=permalink).order_by(Reminder.new_date.asc()).all()
