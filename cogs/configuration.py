import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import logging
from contextlib import contextmanager
from cogs.utils.checks import is_admin
import config

DB_PATH = config.DB_PATH
logger = logging.getLogger(__name__)

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}", exc_info=True)
        raise
    finally:
        conn.close()

def init_guild_tables():
    """Initialize guild configuration tables"""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS guild_config (
                guild_id INTEGER PRIMARY KEY,
                prefix TEXT DEFAULT '?',
                spam_filter_enabled INTEGER DEFAULT 1,
                leveling_enabled INTEGER DEFAULT 1,
                welcome_enabled INTEGER DEFAULT 1,
                join_dm_enabled INTEGER DEFAULT 0,
                join_dm_message TEXT DEFAULT NULL,
                error_channel_id INTEGER DEFAULT NULL,
                mod_log_channel_id INTEGER DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS master_users (
                user_id INTEGER PRIMARY KEY,
                added_by INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

class Configuration(commands.Cog):
    """Guild configuration management"""

    def __init__(self, bot):
        self.bot = bot
        self.prefix_cache = {}
        init_guild_tables()

    def get_guild_config(self, guild_id: int) -> dict:
        """Get guild configuration, creating default if not exists"""
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM guild_config WHERE guild_id = ?",
                (guild_id,)
            ).fetchone()
            if row:
                return dict(row)
            # Create default config
            conn.execute(
                "INSERT INTO guild_config (guild_id) VALUES (?)",
                (guild_id,)
            )
            return {
                "guild_id": guild_id,
                "prefix": "?",
                "spam_filter_enabled": 1,
                "leveling_enabled": 1,
                "welcome_enabled": 1,
                "join_dm_enabled": 0,
                "join_dm_message": None,
                "error_channel_id": None,
                "mod_log_channel_id": None
            }

    # === PREFIX COMMANDS ===
    @commands.command(name="set-prefix", aliases=["setprefix", "prefix"])
    @is_admin()
    async def set_prefix(self, ctx, new_prefix: str):
        """Set the command prefix for this server"""
        if len(new_prefix) > 10:
            return await ctx.send("Prefix must be 10 characters or less.")

        with get_db() as conn:
            conn.execute("""
                INSERT INTO guild_config (guild_id, prefix) VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET prefix = ?, updated_at = CURRENT_TIMESTAMP
            """, (ctx.guild.id, new_prefix, new_prefix))

        self.prefix_cache[ctx.guild.id] = new_prefix
        embed = discord.Embed(
            title="Prefix Updated",
            description=f"Command prefix set to `{new_prefix}`",
            color=config.COLOR_SUCCESS
        )
        await ctx.send(embed=embed)

    @commands.command(name="get-prefix", aliases=["getprefix"])
    async def get_prefix(self, ctx):
        """Show the current command prefix"""
        cfg = self.get_guild_config(ctx.guild.id)
        await ctx.send(f"Current prefix: `{cfg['prefix']}`")

    # === INIT GUILD ===
    @commands.command(name="init-guild", aliases=["initguild", "setup"])
    @is_admin()
    async def init_guild(self, ctx):
        """Initialize all guild settings and database tables"""
        guild_id = ctx.guild.id

        with get_db() as conn:
            # Ensure guild_config exists
            conn.execute("""
                INSERT OR IGNORE INTO guild_config (guild_id) VALUES (?)
            """, (guild_id,))

            # Ensure glevel table has guild entry
            conn.execute("""
                INSERT OR IGNORE INTO glevel (guild_id, enabled) VALUES (?, 'enabled')
            """, (guild_id,))

            # Ensure welcome table exists
            conn.execute("""
                INSERT OR IGNORE INTO welcome (guild_id) VALUES (?)
            """, (guild_id,))

        embed = discord.Embed(
            title="Guild Initialized",
            description=f"**{ctx.guild.name}** has been set up!",
            color=config.COLOR_SUCCESS
        )
        embed.add_field(name="Prefix", value="`?`", inline=True)
        embed.add_field(name="Leveling", value="Enabled", inline=True)
        embed.add_field(name="Spam Filter", value="Enabled", inline=True)
        embed.set_footer(text="Use ?config to view all settings")
        await ctx.send(embed=embed)

    # === CONFIG VIEW/EDIT ===
    @commands.command(name="config", aliases=["settings", "cfg"])
    @is_admin()
    async def show_config(self, ctx):
        """Show all guild configuration settings"""
        cfg = self.get_guild_config(ctx.guild.id)

        embed = discord.Embed(
            title=f"Configuration for {ctx.guild.name}",
            color=config.COLOR_INFO
        )
        embed.add_field(name="Prefix", value=f"`{cfg['prefix']}`", inline=True)
        embed.add_field(
            name="Spam Filter",
            value="Enabled" if cfg['spam_filter_enabled'] else "Disabled",
            inline=True
        )
        embed.add_field(
            name="Leveling",
            value="Enabled" if cfg['leveling_enabled'] else "Disabled",
            inline=True
        )
        embed.add_field(
            name="Welcome Messages",
            value="Enabled" if cfg['welcome_enabled'] else "Disabled",
            inline=True
        )
        embed.add_field(
            name="Join DM",
            value="Enabled" if cfg['join_dm_enabled'] else "Disabled",
            inline=True
        )

        if cfg['mod_log_channel_id']:
            embed.add_field(
                name="Mod Log Channel",
                value=f"<#{cfg['mod_log_channel_id']}>",
                inline=True
            )

        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
        await ctx.send(embed=embed)

    # === SPAM FILTER TOGGLE ===
    @commands.command(name="set-spamfilter", aliases=["spamfilter", "togglespam"])
    @is_admin()
    async def set_spamfilter(self, ctx, state: str):
        """Enable or disable the spam filter (on/off)"""
        state = state.lower()
        if state not in ("on", "off", "enable", "disable", "1", "0", "true", "false"):
            return await ctx.send("Usage: `?set-spamfilter on` or `?set-spamfilter off`")

        enabled = state in ("on", "enable", "1", "true")

        with get_db() as conn:
            conn.execute("""
                INSERT INTO guild_config (guild_id, spam_filter_enabled) VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET spam_filter_enabled = ?, updated_at = CURRENT_TIMESTAMP
            """, (ctx.guild.id, int(enabled), int(enabled)))

        status = "enabled" if enabled else "disabled"
        embed = discord.Embed(
            title="Spam Filter Updated",
            description=f"Spam filter has been **{status}**",
            color=config.COLOR_SUCCESS if enabled else config.COLOR_WARNING
        )
        await ctx.send(embed=embed)

    # === LEVELING TOGGLE ===
    @commands.command(name="set-leveling", aliases=["toggleleveling", "setxp"])
    @is_admin()
    async def set_leveling(self, ctx, state: str):
        """Enable or disable the leveling system (on/off)"""
        state = state.lower()
        if state not in ("on", "off", "enable", "disable", "1", "0", "true", "false"):
            return await ctx.send("Usage: `?set-leveling on` or `?set-leveling off`")

        enabled = state in ("on", "enable", "1", "true")

        with get_db() as conn:
            conn.execute("""
                INSERT INTO guild_config (guild_id, leveling_enabled) VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET leveling_enabled = ?, updated_at = CURRENT_TIMESTAMP
            """, (ctx.guild.id, int(enabled), int(enabled)))
            # Also update glevel table
            conn.execute("""
                INSERT INTO glevel (guild_id, enabled) VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET enabled = ?
            """, (ctx.guild.id, "enabled" if enabled else "disabled", "enabled" if enabled else "disabled"))

        status = "enabled" if enabled else "disabled"
        embed = discord.Embed(
            title="Leveling System Updated",
            description=f"Leveling has been **{status}**",
            color=config.COLOR_SUCCESS if enabled else config.COLOR_WARNING
        )
        await ctx.send(embed=embed)

    # === JOIN MESSAGE ===
    @commands.command(name="set-joinmessage", aliases=["setjoinmsg", "joindm"])
    @is_admin()
    async def set_join_message(self, ctx, *, message: str = None):
        """Set the DM message sent to new members. Use 'off' to disable."""
        if message is None:
            cfg = self.get_guild_config(ctx.guild.id)
            if cfg['join_dm_message']:
                await ctx.send(f"Current join message:\n```{cfg['join_dm_message']}```")
            else:
                await ctx.send("No join message set. Use `?set-joinmessage <message>` to set one.")
            return

        if message.lower() in ("off", "disable", "none", "clear"):
            with get_db() as conn:
                conn.execute("""
                    UPDATE guild_config SET join_dm_enabled = 0, join_dm_message = NULL, updated_at = CURRENT_TIMESTAMP
                    WHERE guild_id = ?
                """, (ctx.guild.id,))
            return await ctx.send("Join DM disabled.")

        with get_db() as conn:
            conn.execute("""
                INSERT INTO guild_config (guild_id, join_dm_enabled, join_dm_message) VALUES (?, 1, ?)
                ON CONFLICT(guild_id) DO UPDATE SET join_dm_enabled = 1, join_dm_message = ?, updated_at = CURRENT_TIMESTAMP
            """, (ctx.guild.id, message, message))

        embed = discord.Embed(
            title="Join Message Set",
            description="New members will receive this DM:",
            color=config.COLOR_SUCCESS
        )
        embed.add_field(name="Message", value=message[:1024], inline=False)
        embed.set_footer(text="Variables: {user}, {server}, {membercount}")
        await ctx.send(embed=embed)

    # === MOD LOG CHANNEL ===
    @commands.command(name="set-modlog", aliases=["modlog", "setlogchannel"])
    @is_admin()
    async def set_mod_log(self, ctx, channel: discord.TextChannel = None):
        """Set the channel for moderation logs"""
        if channel is None:
            with get_db() as conn:
                conn.execute("""
                    UPDATE guild_config SET mod_log_channel_id = NULL, updated_at = CURRENT_TIMESTAMP
                    WHERE guild_id = ?
                """, (ctx.guild.id,))
            return await ctx.send("Mod log channel cleared.")

        with get_db() as conn:
            conn.execute("""
                INSERT INTO guild_config (guild_id, mod_log_channel_id) VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET mod_log_channel_id = ?, updated_at = CURRENT_TIMESTAMP
            """, (ctx.guild.id, channel.id, channel.id))

        embed = discord.Embed(
            title="Mod Log Channel Set",
            description=f"Moderation actions will be logged to {channel.mention}",
            color=config.COLOR_SUCCESS
        )
        await ctx.send(embed=embed)

    # === MASTER USERS ===
    @commands.command(name="add-masteruser", aliases=["addmaster"])
    @commands.is_owner()
    async def add_master_user(self, ctx, user: discord.User):
        """Add a master user (bot owner only)"""
        with get_db() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO master_users (user_id, added_by) VALUES (?, ?)
            """, (user.id, ctx.author.id))

        embed = discord.Embed(
            title="Master User Added",
            description=f"{user.mention} is now a master user",
            color=config.COLOR_SUCCESS
        )
        await ctx.send(embed=embed)

    @commands.command(name="remove-masteruser", aliases=["delmaster", "removemaster"])
    @commands.is_owner()
    async def remove_master_user(self, ctx, user: discord.User):
        """Remove a master user (bot owner only)"""
        with get_db() as conn:
            conn.execute("DELETE FROM master_users WHERE user_id = ?", (user.id,))

        embed = discord.Embed(
            title="Master User Removed",
            description=f"{user.mention} is no longer a master user",
            color=config.COLOR_WARNING
        )
        await ctx.send(embed=embed)

    @commands.command(name="list-masterusers", aliases=["masters", "listmasters"])
    @commands.is_owner()
    async def list_master_users(self, ctx):
        """List all master users"""
        with get_db() as conn:
            rows = conn.execute("SELECT user_id FROM master_users").fetchall()

        if not rows:
            return await ctx.send("No master users configured.")

        users = []
        for row in rows:
            try:
                user = await self.bot.fetch_user(row['user_id'])
                users.append(f"- {user} (`{user.id}`)")
            except discord.NotFound:
                users.append(f"- Unknown (`{row['user_id']}`)")

        embed = discord.Embed(
            title="Master Users",
            description="\n".join(users),
            color=config.COLOR_INFO
        )
        await ctx.send(embed=embed)

    # === ERROR CHANNEL ===
    @commands.command(name="drop-errors-on", aliases=["errorson", "seterrors"])
    @commands.is_owner()
    async def set_error_channel(self, ctx, channel: discord.TextChannel = None):
        """Set channel for error logging (bot owner only)"""
        if channel is None:
            with get_db() as conn:
                conn.execute("""
                    UPDATE guild_config SET error_channel_id = NULL, updated_at = CURRENT_TIMESTAMP
                    WHERE guild_id = ?
                """, (ctx.guild.id,))
            return await ctx.send("Error logging channel cleared.")

        with get_db() as conn:
            conn.execute("""
                INSERT INTO guild_config (guild_id, error_channel_id) VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET error_channel_id = ?, updated_at = CURRENT_TIMESTAMP
            """, (ctx.guild.id, channel.id, channel.id))

        embed = discord.Embed(
            title="Error Channel Set",
            description=f"Errors will be logged to {channel.mention}",
            color=config.COLOR_SUCCESS
        )
        await ctx.send(embed=embed)

    # === SLASH COMMANDS ===
    @app_commands.command(name="config", description="View server configuration")
    @app_commands.default_permissions(administrator=True)
    async def slash_config(self, interaction: discord.Interaction):
        """Slash command version of config"""
        cfg = self.get_guild_config(interaction.guild_id)

        embed = discord.Embed(
            title=f"Configuration for {interaction.guild.name}",
            color=config.COLOR_INFO
        )
        embed.add_field(name="Prefix", value=f"`{cfg['prefix']}`", inline=True)
        embed.add_field(
            name="Spam Filter",
            value="Enabled" if cfg['spam_filter_enabled'] else "Disabled",
            inline=True
        )
        embed.add_field(
            name="Leveling",
            value="Enabled" if cfg['leveling_enabled'] else "Disabled",
            inline=True
        )
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="set-prefix", description="Set the command prefix for this server")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(prefix="The new command prefix (max 10 characters)")
    async def slash_set_prefix(self, interaction: discord.Interaction, prefix: str):
        """Slash command to set prefix"""
        if len(prefix) > 10:
            return await interaction.response.send_message(
                "Prefix must be 10 characters or less.",
                ephemeral=True
            )

        with get_db() as conn:
            conn.execute("""
                INSERT INTO guild_config (guild_id, prefix) VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET prefix = ?, updated_at = CURRENT_TIMESTAMP
            """, (interaction.guild_id, prefix, prefix))

        self.prefix_cache[interaction.guild_id] = prefix
        embed = discord.Embed(
            title="Prefix Updated",
            description=f"Command prefix set to `{prefix}`",
            color=config.COLOR_SUCCESS
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Configuration(bot))
    logger.info("Configuration cog loaded")
