from datetime import datetime
from sqlalchemy import func, asc, desc

from core.config import config
from repository.base_repository import BaseRepository
from repository.database import session
from repository.database.user_channels import UserChannel


class UserChannelRepository(BaseRepository):
    # unknown - pending - verified - kicked - banned

    @classmethod
    def increment(
        cls,
        channel_id: int,
        channel_name: str,
        user_id: int,
        user_name: str,
        guild_id: int,
        guild_name: str,
        last_msg_at: datetime,
        count: int,
        is_webhook: bool,
    ):
        """Increment user_channel count, if it doesn't exist, create it"""
        user_channel = (
            session.query(UserChannel)
            .filter_by(channel_id=channel_id, user_id=user_id, guild_id=guild_id)
            .one_or_none()
        )
        if not user_channel:
            session.add(
                UserChannel(
                    guild_id=guild_id,
                    guild_name=user_name,
                    channel_id=channel_id,
                    channel_name=channel_name,
                    user_id=user_id,
                    user_name=user_name,
                    is_webhook=is_webhook,
                    count=count,
                    last_msg_at=last_msg_at,
                )
            )

        else:
            user_channel.count = user_channel.count + count
            if user_channel.last_msg_at < last_msg_at:
                user_channel.last_msg_at = last_msg_at
            if user_channel.channel_name != channel_name:
                user_channel.channel_name = channel_name
            if user_channel.user_name != user_name:
                user_channel.user_name = user_name
            if user_channel.guild_name != guild_name:
                user_channel.guild_name = guild_name

        session.commit()

    @classmethod
    def decrement(
        cls,
        channel_id: int,
        channel_name: str,
        user_id: int,
        user_name: str,
        guild_id: int,
        guild_name: str,
        last_msg_at: datetime,
    ):
        """Decrement user_channel count."""
        user_channel = (
            session.query(UserChannel)
            .filter_by(channel_id=channel_id, user_id=user_id, guild_id=guild_id)
            .one_or_none()
        )
        if not user_channel:
            session.add(
                UserChannel(
                    guild_id=guild_id,
                    guild_name=user_name,
                    channel_id=channel_id,
                    channel_name=channel_name,
                    user_id=user_id,
                    user_name=user_name,
                    count=0,
                    last_msg_at=last_msg_at,
                )
            )

        else:
            user_channel.count = user_channel.count - 1
            if user_channel.last_msg_at < last_msg_at:
                user_channel.last_msg_at = last_msg_at
            if user_channel.channel_name != channel_name:
                user_channel.channel_name = channel_name
            if user_channel.user_name != user_name:
                user_channel.user_name = user_name
            if user_channel.guild_name != guild_name:
                user_channel.guild_name = guild_name

        session.commit()

    @classmethod
    def get_user_channels(cls):
        """Retrieves the whole table"""
        return session.query(UserChannel).all()

    @classmethod
    def get_channel(cls, channel_id: int):
        """Retrieves table, filtered by channel id"""
        return session.query(UserChannel).filter_by(channel_id=channel_id).all()

    @classmethod
    def get_user(cls, user_id: int):
        """Retrieves table, filtered by user id"""
        return session.query(UserChannel).filter_by(user_id=user_id).all()

    @classmethod
    def get_last(
        cls,
        guild_id=None,
        user_id=None,
        channel_id=None,
        webhooks=False,
        include_filtered=False,
    ):
        last_msg_at = func.max(UserChannel.last_msg_at).label("last_msg_at")

        query = session.query(
            UserChannel.guild_id,
            UserChannel.channel_id,
            UserChannel.user_id,
            last_msg_at,
        )

        query = cls._filter(
            query=query,
            guild_id=guild_id,
            user_id=user_id,
            channel_id=channel_id,
            webhooks=webhooks,
            include_filtered=include_filtered,
        )

        result = (
            query.group_by(
                UserChannel.guild_id, UserChannel.channel_id, UserChannel.user_id
            )
            .order_by(desc("last_msg_at"))
            .first()
        )

        return result

    @classmethod
    def get_user_counts(
        cls,
        guild_id=None,
        channel_id=None,
        user_id=None,
        webhooks=False,
        include_filtered=False,
    ):
        query = cls._get_user_query(
            guild_id=guild_id,
            channel_id=channel_id,
            user_id=user_id,
            webhooks=webhooks,
            include_filtered=include_filtered,
        )
        return query.all()

    @classmethod
    def get_channel_counts(
        cls,
        guild_id=None,
        channel_id=None,
        user_id=None,
        webhooks=False,
        include_filtered=False,
    ):
        query = cls._get_channel_query(
            guild_id=guild_id,
            channel_id=channel_id,
            user_id=user_id,
            webhooks=webhooks,
            include_filtered=include_filtered,
        )
        return query.all()

    @classmethod
    def get_user_ranked(
        cls, guild_id=None, user_id=None, webhooks=False, include_filtered=False
    ):
        """Retrieves table, filtered by user id"""
        subquery = cls._get_user_query(
            guild_id=guild_id, webhooks=webhooks, include_filtered=include_filtered
        ).subquery()
        query = session.query(subquery).filter(subquery.c.user_id == user_id)
        result = query.first()
        return result

    @classmethod
    def get_channel_ranked(
        cls, guild_id=None, channel_id=None, webhooks=False, include_filtered=False
    ):
        """Retrieves table, filtered by user id"""
        subquery = cls._get_channel_query(
            guild_id=guild_id, webhooks=webhooks, include_filtered=include_filtered
        ).subquery()
        query = session.query(subquery).filter(subquery.c.channel_id == channel_id)
        result = query.first()
        return result

    @classmethod
    def get_user_sum(
        cls, guild_id=None, user_id=None, webhooks=False, include_filtered=False
    ):
        """Retrieves table, filtered by user id"""
        query = cls._get_user_query(
            guild_id=guild_id,
            user_id=user_id,
            webhooks=webhooks,
            include_filtered=include_filtered,
        )
        result = query.count()
        return result

    @classmethod
    def get_channel_sum(
        cls, guild_id=None, channel_id=None, webhooks=False, include_filtered=False
    ):
        """Retrieves table, filtered by user id"""
        query = cls._get_channel_query(
            guild_id=guild_id,
            channel_id=channel_id,
            webhooks=webhooks,
            include_filtered=include_filtered,
        )
        result = query.count()
        return result

    @classmethod
    def _get_channel_query(
        cls,
        guild_id=None,
        channel_id=None,
        user_id=None,
        webhooks=False,
        include_filtered=False,
    ):
        """Retrieves table, filtered by user id"""
        last_msg_at = func.max(UserChannel.last_msg_at).label("last_msg_at")
        total = func.sum(UserChannel.count).label("total")
        rank = (
            func.dense_rank()
            .over(order_by=[desc(total), asc(last_msg_at)])
            .label("rank")
        )
        query = session.query(
            UserChannel.guild_id,
            UserChannel.guild_name,
            UserChannel.channel_id,
            UserChannel.channel_name,
            last_msg_at,
            total,
            rank,
        )

        query = cls._filter(
            query=query,
            guild_id=guild_id,
            channel_id=channel_id,
            user_id=user_id,
            webhooks=webhooks,
            include_filtered=include_filtered,
        )
        query = query.group_by(
            UserChannel.guild_id,
            UserChannel.guild_name,
            UserChannel.channel_id,
            UserChannel.channel_name,
        ).order_by("rank")

        return query

    @classmethod
    def _get_user_query(
        cls,
        guild_id=None,
        channel_id=None,
        user_id=None,
        webhooks=False,
        include_filtered=False,
    ):
        """Retrieves table, filtered by user id"""
        last_msg_at = func.max(UserChannel.last_msg_at).label("last_msg_at")
        total = func.sum(UserChannel.count).label("total")
        rank = (
            func.dense_rank()
            .over(order_by=[desc(total), asc(last_msg_at)])
            .label("rank")
        )

        query = session.query(
            UserChannel.guild_id,
            UserChannel.guild_name,
            UserChannel.user_id,
            UserChannel.user_name,
            last_msg_at,
            total,
            rank,
        )
        query = cls._filter(
            query=query,
            guild_id=guild_id,
            channel_id=channel_id,
            user_id=user_id,
            webhooks=webhooks,
            include_filtered=include_filtered,
        )
        query = query.group_by(
            UserChannel.guild_id,
            UserChannel.guild_name,
            UserChannel.user_id,
            UserChannel.user_name,
        ).order_by("rank")

        return query

    @classmethod
    def _filter(
        cls,
        query=None,
        guild_id=None,
        channel_id=None,
        user_id=None,
        webhooks=False,
        include_filtered=False,
    ):
        if query is None:
            return None

        if not webhooks:
            query = query.filter_by(is_webhook=False)

        if guild_id is not None:
            query = query.filter_by(guild_id=guild_id)

        if channel_id is not None:
            query = query.filter_by(channel_id=channel_id)

        if user_id is not None:
            query = query.filter_by(user_id=user_id)

        if not include_filtered:
            query = query.filter(
                UserChannel.user_id.notin_(config.board_ignored_users)
            ).filter(UserChannel.channel_id.notin_(config.board_ignored_channels))

        return query

    @classmethod
    def update_user(cls, user_id=None, user_name=None):
        if user_id is None or user_name is None:
            return None
        users = session.query(UserChannel).filter_by(user_id=user_id).all()
        for user in users:
            if user.user_name != user_name:
                user.user_name = user_name
        session.commit()

    @classmethod
    def update_channel(cls, channel_id=None, channel_name=None):
        if channel_id is None or channel_name is None:
            return None
        channels = session.query(UserChannel).filter_by(channel_id=channel_id).all()
        for channel in channels:
            if channel.channel_name != channel_name:
                channel.channel_name = channel_name
        session.commit()

    @classmethod
    def update_guild(cls, guild_id=None, guild_name=None):
        if guild_id is None or guild_name is None:
            return None
        guilds = session.query(UserChannel).filter_by(guild_id=guild_id).all()
        for guild in guilds:
            if guild.guild_name != guild_name:
                guild.guild_name = guild_name
        session.commit()

    @classmethod
    def delete_channel(cls, channel_id=None):
        if channel_id is None:
            return None
        users = session.query(UserChannel).filter_by(channel_id=channel_id).all()

        for item in users:
            session.delete(item)

        session.commit()
