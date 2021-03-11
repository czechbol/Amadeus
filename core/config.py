import sys
import json


class Config:
    def get(self, group: str, key: str):
        if group in self.c and key in self.c.get(group):
            v = self.c.get(group).get(key)
        elif key in self.d.get(group):
            v = self.d.get(group).get(key)
        else:
            v = None

        if v is not None:
            return v

        raise AttributeError("Configuration file: key not found")

    def __init__(self):
        try:
            self.d = json.load(open("config/config.default.json", "r"))
            self.c = json.load(open("config/config.json", "r"))
        except FileNotFoundError:
            print("Error loading config files.")
            sys.exit(1)

        # DATABASE
        self.db_states = self.get("database", "states")
        self.db_string = self.get("database", "string")

        # BOT
        self.debug = self.get("bot", "debug")
        self.loader = self.get("bot", "loader")
        self.key = self.get("bot", "key")
        self.admin_id = self.get("bot", "admin id")
        self.guild_id = self.get("bot", "guild id")
        self.slave_id = self.get("bot", "slave guild id")
        self.host = self.get("bot", "host")
        self.prefixes = self.get("bot", "prefixes")
        self.prefix = self.prefixes[0]

        self.extensions = self.get("bot", "extensions")

        # CHANNELS
        self.channel_mods = self.get("channels", "mods")
        self.channel_boost = self.get("channels", "boost")
        self.channel_botdev = self.get("channels", "botdev")
        self.channel_guildlog = self.get("channels", "guildlog")
        self.channel_botspam = self.get("channels", "botspam")
        self.bot_allowed = self.get("channels", "bot allowed")

        # COLOR
        self.color = self.get("color", "main")
        self.color_success = self.get("color", "success")
        self.color_notify = self.get("color", "notify")
        self.color_error = self.get("color", "error")
        self.color_boost = self.get("color", "boost")
        self.colors = [
            self.color,
            self.color_success,
            self.color_notify,
            self.color_error,
            self.color_boost,
        ]

        # DELAY
        self.delay_embed = self.get("delay", "embed")

        # ROLES
        self.role_verify = self.get("roles", "verify_id")
        self.role_mod = self.get("roles", "mod_id")
        self.roles_elevated = self.get("roles", "elevated_ids")
        self.roles_unverify = self.get("roles", "unverify_ids")
        self.booster_role = self.get("roles", "server_booster")

        # BOARDS
        self.board_ignored_channels = self.get("boards", "ignored channels")
        self.board_ignored_users = self.get("boards", "ignored users")
        self.board_top = self.get("boards", "top number")
        self.board_around = self.get("boards", "around number")

        # COMPATIBILITY
        self.noimitation = self.get("compatibility", "ignored imitation channels")


config = Config()
