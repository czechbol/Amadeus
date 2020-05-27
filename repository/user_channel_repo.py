from datetime import datetime
from datetime import timedelta

from repository.base_repository import BaseRepository
from repository.database import session
from repository.database.user_channels import UserChannel


class UserChannelRepository(BaseRepository):
    # unknown - pending - verified - kicked - banned

    def increment(
        self,
        channel_id: int,
        user_id: int,
        guild_id: int,
        last_message_id: int,
        last_message_at: datetime,
    ):
        """Increment user_channel count, 
        if it doesn't exist, create it"""
        user_channel = (
            session.query(UserChannel)
            .filter_by(channel_id=channel_id, user_id=user_id, guild_id=guild_id)
            .one_or_none()
        )
        if not user_channel:
            session.add(
                UserChannel(
                    channel_id=channel_id,
                    user_id=user_id,
                    last_message_at=last_message_at,
                    last_message_id=last_message_id,
                    guild_id=guild_id,
                )
            )

        else:
            user_channel.count = user_channel.count + 1
            if user_channel.last_message_at < last_message_at:
                user_channel.last_message_at = last_message_at
                user_channel.last_message_id = last_message_id

        session.commit()

    def decrement(
        self,
        channel_id: int,
        user_id: int,
        guild_id: int,
        last_message_id: int,
        last_message_at: datetime,
    ):
        """Increment user_channel count, 
        if it doesn't exist, create it"""
        user_channel = (
            session.query(UserChannel)
            .filter_by(channel_id=channel_id, user_id=user_id, guild_id=guild_id)
            .one_or_none()
        )
        if not user_channel:
            session.add(
                UserChannel(
                    channel_id=channel_id,
                    user_id=user_id,
                    count=0,
                    last_message_at=last_message_at,
                    last_message_id=last_message_id,
                    guild_id=guild_id,
                )
            )

        else:
            user_channel.count = user_channel.count - 1
            if user_channel.last_message_at < last_message_at:
                user_channel.last_message_at = last_message_at
                user_channel.last_message_id = last_message_id

        session.commit()

    def get_channels(self):
        """Update a specified user with a new verification code"""
        channels = session.query(UserChannel).all()
        result = []

        if channels is not None:
            for ch in channels:
                result.append(ch.__dict__)
        else:
            result = None
        return result

    def get_channel(self, channel_id: int):
        """Update a specified user with a new verification code"""
        channels = session.query(UserChannel).filter_by(channel_id=channel_id)
        result = []

        if channels is not None:
            for ch in channels:
                ch = ch.__dict__
                for row in result:
                    if row["channel_id"] == ch["channel_id"] and row["guild_id"] == ch["guild_id"]:
                        row["count"] += ch["count"]
                        if row["last_message_at"] < ch["last_message_at"]:
                            row["last_message_at"] = ch["last_message_at"]
                        break
                else:
                    result.append(
                        {
                            "channel_id": ch["channel_id"],
                            "guild_id": ch["guild_id"],
                            "count": ch["count"],
                            "last_message_at": ch["last_message_at"],
                        }
                    )
        else:
            result = None
        return result

    def get_users(self):
        users = session.query(UserChannel).all()
        result = []

        if users is not None:
            for usr in users:
                usr = usr.__dict__
                for row in result:
                    if row["user_id"] == usr["user_id"]:
                        row["count"] += usr["count"]
                        if row["last_message_at"] < usr["last_message_at"]:
                            row["last_message_at"] = usr["last_message_at"]
                        break
                else:
                    result.append(
                        {
                            "user_id": usr["user_id"],
                            "count": usr["count"],
                            "last_message_at": usr["last_message_at"],
                        }
                    )
        else:
            result = None
        return result

    def get_user(self, user_id: int):
        users = session.query(UserChannel).filter_by(user_id=user_id)
        result = []

        if users is not None:
            for usr in users:
                usr = usr.__dict__
                for row in result:
                    if row["user_id"] == usr["user_id"]:
                        row["count"] += usr["count"]
                        if row["last_message_at"] < usr["last_message_at"]:
                            row["last_message_at"] = usr["last_message_at"]
                        break
                else:
                    result.append(
                        {
                            "user_id": usr["user_id"],
                            "count": usr["count"],
                            "last_message_at": usr["last_message_at"],
                        }
                    )
        else:
            result = None
        return result

    def del_vote(self, channel_id: int = None, message_id: int = None):
        users = (
            session.query(Vote)
            .filter(Vote.message_id == message_id)
            .filter(Vote.channel_id == channel_id)
            .delete()
        )
        session.commit()
        return users
