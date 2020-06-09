import datetime

from repository.base_repository import BaseRepository
from repository.database import session
from repository.database.image import Image


class ImageRepository(BaseRepository):
    @classmethod
    def add_image(cls, channel_id: int, message_id: int, attachment_id: int, dhash: str):
        """Add new image hash"""
        session.add(
            Image(
                channel_id=channel_id,
                message_id=message_id,
                attachment_id=attachment_id,
                dhash=dhash,
                timestamp=datetime.datetime.now().replace(microsecond=0),
            )
        )
        session.commit()

    @classmethod
    def getHash(cls, dhash: str):
        return session.query(Image).filter(Image.dhash == dhash).all()

    @classmethod
    def getAll(cls):
        return session.query(Image)

    @classmethod
    def getLast(cls, num: int):
        return session.query(Image)[:num]

    @classmethod
    def deleteByMessage(cls, message_id: int):
        session.query(Image).filter(Image.message_id == message_id).delete()
        session.commit()
