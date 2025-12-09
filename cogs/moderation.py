import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import datetime
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

def init_mod_tables():
    """Initialize moderation tables"""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mod_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                target_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                reason TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_mod_guild ON mod_actions(guild_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_mod_moderator ON mod_actions(moderator_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_mod_target ON mod_actions(target_id)
        """)

class Moderation(commands.Cog):
    """Enhanced moderation commands with action logging"""

    def __init__(self, bot):
        self.bot = bot
        init_mod_tables()

    def log_action(self, guild_id: int, moderator_id: int, target_id: int, action: str, reason: str = None):
        """Log a moderation action to the database"""
        with get_db() as conn:
            conn.execute("""
                INSERT INTO mod_actions (guild_id, moderator_id, target_id, action, reason)
                VALUES (?, ?, ?, ?, ?)
            """, (guild_id, moderator_id, target_id, action, reason))

    async def send_mod_log(self, guild: discord.Guild, embed: discord.Embed):
        """Send to mod log channel if configured"""
        with get_db() as conn:
            row = conn.execute("""
                SELECT mod_log_channel_id FROM guild_config WHERE guild_id = ?
            """, (guild.id,)).fetchone()

        if row and row['mod_log_channel_id']:
            channel = guild.get_channel(row['mod_log_channel_id'])
            if channel:
                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    pass

    # === KICK ===
    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Kick a member from the server"""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send("Cannot kick someone with equal or higher role.")

        try:
            await member.kick(reason=f"{reason} | By: {ctx.author}")
        except discord.Forbidden:
            return await ctx.send("I don't have permission to kick this user.")

        self.log_action(ctx.guild.id, ctx.author.id, member.id, "kick", reason)

        embed = discord.Embed(
            title="Member Kicked",
            color=config.COLOR_WARNING
        )
        embed.add_field(name="User", value=f"{member} (`{member.id}`)", inline=False)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()

        await ctx.send(embed=embed)
        await self.send_mod_log(ctx.guild, embed)

    # === TIMEOUT ===
    @commands.command(name="timeout", aliases=["mute", "to"])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member, duration: str, *, reason: str = "No reason provided"):
        """Timeout a member

        Duration examples: 10m, 1h, 1d, 1w
        """
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send("Cannot timeout someone with equal or higher role.")

        # Parse duration
        duration_map = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400,
            'w': 604800
        }

        try:
            unit = duration[-1].lower()
            amount = int(duration[:-1])
            if unit not in duration_map:
                raise ValueError
            seconds = amount * duration_map[unit]
        except (ValueError, IndexError):
            return await ctx.send("Invalid duration. Use format: 10m, 1h, 1d, 1w")

        if seconds > 2419200:  # 28 days max
            return await ctx.send("Maximum timeout is 28 days.")

        delta = datetime.timedelta(seconds=seconds)

        try:
            await member.timeout(delta, reason=f"{reason} | By: {ctx.author}")
        except discord.Forbidden:
            return await ctx.send("I don't have permission to timeout this user.")

        self.log_action(ctx.guild.id, ctx.author.id, member.id, "timeout", f"{duration} - {reason}")

        embed = discord.Embed(
            title="Member Timed Out",
            color=config.COLOR_WARNING
        )
        embed.add_field(name="User", value=f"{member} (`{member.id}`)", inline=False)
        embed.add_field(name="Duration", value=duration, inline=True)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()

        await ctx.send(embed=embed)
        await self.send_mod_log(ctx.guild, embed)

    # === UNTIMEOUT ===
    @commands.command(name="untimeout", aliases=["unmute"])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def untimeout(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Remove timeout from a member"""
        try:
            await member.timeout(None, reason=f"{reason} | By: {ctx.author}")
        except discord.Forbidden:
            return await ctx.send("I don't have permission to remove timeout.")

        self.log_action(ctx.guild.id, ctx.author.id, member.id, "untimeout", reason)

        embed = discord.Embed(
            title="Timeout Removed",
            description=f"{member.mention} can speak again.",
            color=config.COLOR_SUCCESS
        )
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=True)
        await ctx.send(embed=embed)

    # === WARN ===
    @commands.command(name="warn")
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Warn a member (logged but no automatic action)"""
        self.log_action(ctx.guild.id, ctx.author.id, member.id, "warn", reason)

        embed = discord.Embed(
            title="Member Warned",
            color=config.COLOR_WARNING
        )
        embed.add_field(name="User", value=f"{member} (`{member.id}`)", inline=False)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()

        await ctx.send(embed=embed)
        await self.send_mod_log(ctx.guild, embed)

        # DM the user
        try:
            dm_embed = discord.Embed(
                title=f"Warning from {ctx.guild.name}",
                description=f"You have been warned by a moderator.",
                color=config.COLOR_WARNING
            )
            dm_embed.add_field(name="Reason", value=reason, inline=False)
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            pass

    # === MOD STATS ===
    @commands.command(name="mod-stats", aliases=["modstats", "modlog"])
    @is_admin()
    async def mod_stats(self, ctx, moderator: discord.Member = None):
        """Show moderation statistics

        Usage:
        ?mod-stats - Show all mod stats
        ?mod-stats @Mod - Show specific moderator's stats
        """
        with get_db() as conn:
            if moderator:
                # Stats for specific moderator
                rows = conn.execute("""
                    SELECT action, COUNT(*) as count FROM mod_actions
                    WHERE guild_id = ? AND moderator_id = ?
                    GROUP BY action
                """, (ctx.guild.id, moderator.id)).fetchall()

                total = conn.execute("""
                    SELECT COUNT(*) as count FROM mod_actions
                    WHERE guild_id = ? AND moderator_id = ?
                """, (ctx.guild.id, moderator.id)).fetchone()['count']

                embed = discord.Embed(
                    title=f"Mod Stats for {moderator.display_name}",
                    color=config.COLOR_INFO
                )
                embed.set_thumbnail(url=moderator.display_avatar.url)
            else:
                # Overall stats
                rows = conn.execute("""
                    SELECT action, COUNT(*) as count FROM mod_actions
                    WHERE guild_id = ?
                    GROUP BY action
                """, (ctx.guild.id,)).fetchall()

                total = conn.execute("""
                    SELECT COUNT(*) as count FROM mod_actions WHERE guild_id = ?
                """, (ctx.guild.id,)).fetchone()['count']

                # Top moderators
                top_mods = conn.execute("""
                    SELECT moderator_id, COUNT(*) as count FROM mod_actions
                    WHERE guild_id = ?
                    GROUP BY moderator_id
                    ORDER BY count DESC
                    LIMIT 5
                """, (ctx.guild.id,)).fetchall()

                embed = discord.Embed(
                    title=f"Moderation Stats for {ctx.guild.name}",
                    color=config.COLOR_INFO
                )

                if top_mods:
                    top_text = []
                    for row in top_mods:
                        member = ctx.guild.get_member(row['moderator_id'])
                        name = member.display_name if member else f"Unknown ({row['moderator_id']})"
                        top_text.append(f"**{name}**: {row['count']} actions")
                    embed.add_field(name="Top Moderators", value="\n".join(top_text), inline=False)

        if not rows:
            return await ctx.send("No moderation actions recorded.")

        action_stats = {row['action']: row['count'] for row in rows}

        stats_text = []
        for action in ['ban', 'kick', 'timeout', 'warn', 'unban', 'untimeout']:
            count = action_stats.get(action, 0)
            if count > 0:
                emoji = {
                    'ban': '',
                    'kick': '',
                    'timeout': '',
                    'warn': '',
                    'unban': '',
                    'untimeout': ''
                }.get(action, '')
                stats_text.append(f"{emoji} **{action.title()}**: {count}")

        embed.add_field(name="Action Breakdown", value="\n".join(stats_text) or "None", inline=False)
        embed.add_field(name="Total Actions", value=str(total), inline=True)

        await ctx.send(embed=embed)

    # === USER HISTORY ===
    @commands.command(name="history", aliases=["modhistory", "userhistory"])
    @is_admin()
    async def user_history(self, ctx, user: discord.User):
        """View moderation history for a user"""
        with get_db() as conn:
            rows = conn.execute("""
                SELECT action, reason, moderator_id, timestamp FROM mod_actions
                WHERE guild_id = ? AND target_id = ?
                ORDER BY timestamp DESC
                LIMIT 10
            """, (ctx.guild.id, user.id)).fetchall()

        if not rows:
            return await ctx.send(f"No moderation history for {user}")

        embed = discord.Embed(
            title=f"Mod History for {user}",
            color=config.COLOR_INFO
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        for row in rows:
            mod = ctx.guild.get_member(row['moderator_id'])
            mod_name = mod.display_name if mod else f"Unknown ({row['moderator_id']})"

            timestamp = row['timestamp'][:16] if row['timestamp'] else "Unknown"

            embed.add_field(
                name=f"{row['action'].upper()} - {timestamp}",
                value=f"By: {mod_name}\nReason: {row['reason'] or 'None'}",
                inline=False
            )

        await ctx.send(embed=embed)

    # === SLASH COMMANDS ===
    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.default_permissions(kick_members=True)
    @app_commands.describe(member="The member to kick", reason="Reason for the kick")
    async def slash_kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Slash command for kick"""
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            return await interaction.response.send_message("Cannot kick someone with equal or higher role.", ephemeral=True)

        try:
            await member.kick(reason=f"{reason} | By: {interaction.user}")
        except discord.Forbidden:
            return await interaction.response.send_message("I don't have permission to kick this user.", ephemeral=True)

        self.log_action(interaction.guild_id, interaction.user.id, member.id, "kick", reason)

        embed = discord.Embed(title="Member Kicked", color=config.COLOR_WARNING)
        embed.add_field(name="User", value=f"{member}", inline=True)
        embed.add_field(name="Reason", value=reason, inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="timeout", description="Timeout a member")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.describe(
        member="The member to timeout",
        minutes="Timeout duration in minutes",
        reason="Reason for the timeout"
    )
    async def slash_timeout(self, interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "No reason provided"):
        """Slash command for timeout"""
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            return await interaction.response.send_message("Cannot timeout someone with equal or higher role.", ephemeral=True)

        if minutes > 40320:  # 28 days in minutes
            return await interaction.response.send_message("Maximum timeout is 28 days.", ephemeral=True)

        delta = datetime.timedelta(minutes=minutes)

        try:
            await member.timeout(delta, reason=f"{reason} | By: {interaction.user}")
        except discord.Forbidden:
            return await interaction.response.send_message("I don't have permission to timeout this user.", ephemeral=True)

        self.log_action(interaction.guild_id, interaction.user.id, member.id, "timeout", f"{minutes}m - {reason}")

        embed = discord.Embed(title="Member Timed Out", color=config.COLOR_WARNING)
        embed.add_field(name="User", value=f"{member}", inline=True)
        embed.add_field(name="Duration", value=f"{minutes} minutes", inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
    logger.info("Moderation cog loaded")
