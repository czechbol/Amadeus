import discord

from repository.base_repository import BaseRepository
from repository.database import session
from repository.database.emote import Emote


class EmoteRepository(BaseRepository):
    # unknown - pending - verified - kicked - banned

    @classmethod
    def add(cls, emote: discord.Emoji):
        """Add new emote"""
        db_emote = session.query(Emote).filter(Emote.emote_id == emote.id).one_or_none()
        if db_emote is None:
            session.add(
                Emote(
                    emote_id=emote.id,
                    guild_id=emote.guild_id,
                    name=emote.name,
                    animated=emote.animated,
                    original_name=emote.name,
                )
            )
            session.commit()

    @classmethod
    def update(cls, emote: discord.Emoji):
        """Add new emote"""
        db_emote = session.query(Emote).filter(Emote.emote_id == emote.id).one_or_none()

        if db_emote is not None:
            if db_emote.name != emote.name:
                db_emote.name = emote.name
            session.commit()

    @classmethod
    def get_all(cls):
        """Return all emotes"""
        return session.query(Emote).all()
