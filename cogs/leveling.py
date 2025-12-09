import discord
from discord.ext import commands
import sqlite3
import datetime
import math
import random
import asyncio
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

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_tasks = {}

    # === RANKS ===
    @commands.group(invoke_without_command=True)
    async def ranks(self, ctx):
        await ctx.send("`?ranks add` • `?ranks remove` • `?ranks list`")

    @ranks.command()
    @is_admin()
    async def add(self, ctx):
        await ctx.send("Send role name (exact):")
        def check(m): return m.author == ctx.author and m.channel == ctx.channel
        try:
            name_msg = await self.bot.wait_for("message", check=check, timeout=60)
            role = discord.utils.get(ctx.guild.roles, name=name_msg.content)
            if not role: return await ctx.send("Role not found.")

            await ctx.send("Send required level:")
            level_msg = await self.bot.wait_for("message", check=check, timeout=60)
            level = int(level_msg.content)

            with get_db() as conn:
                conn.execute("INSERT OR REPLACE INTO ranks(guild_id, role_id, level) VALUES(?, ?, ?)",
                            (ctx.guild.id, role.id, level))
            await ctx.send(f"{role.name} → Level {level}")
        except asyncio.TimeoutError:
            await ctx.send("Timed out.")

    @ranks.command()
    @is_admin()
    async def remove(self, ctx):
        await ctx.send("Send role name to remove:")
        def check(m): return m.author == ctx.author and m.channel == ctx.channel
        msg = await self.bot.wait_for("message", check=check, timeout=60)
        role = discord.utils.get(ctx.guild.roles, name=msg.content)
        if not role: return await ctx.send("Not found.")

        with get_db() as conn:
            conn.execute("DELETE FROM ranks WHERE guild_id = ? AND role_id = ?", (ctx.guild.id, role.id))
        await ctx.send("Removed.")

    @ranks.command(name="list")
    async def _list(self, ctx):
        with get_db() as conn:
            rows = conn.execute("SELECT role_id, level FROM ranks WHERE guild_id = ?", (ctx.guild.id,)).fetchall()
            if not rows:
                return await ctx.send("No ranks set.")
            text = "\n".join(f"<@&{r['role_id']}> → Level {r['level']}" for r in rows)
        await ctx.send(text)

    # === LEVELING TOGGLE ===
    @commands.group()
    async def leveling(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("`?leveling enable` / `?leveling disable`")

    @leveling.command()
    @is_admin()
    async def enable(self, ctx):
        with get_db() as conn:
            conn.execute("INSERT OR REPLACE INTO glevel(guild_id, enabled) VALUES(?, 'enabled')", (ctx.guild.id,))
        await ctx.send("Leveling enabled.")

    @leveling.command()
    @is_admin()
    async def disable(self, ctx):
        with get_db() as conn:
            conn.execute("INSERT OR REPLACE INTO glevel(guild_id, enabled) VALUES(?, 'disabled')", (ctx.guild.id,))
        await ctx.send("Leveling disabled.")

    # === CORE XP ===
    async def give_xp(self, member: discord.Member, xp: int):
        if member.bot: return

        with get_db() as conn:
            row = conn.execute("SELECT exp, level FROM glevel WHERE guild_id = ? AND user_id = ?",
                              (member.guild.id, member.id)).fetchone()
            if not row:
                conn.execute("INSERT INTO glevel(guild_id, user_id, exp, level) VALUES(?, ?, ?, ?)",
                            (member.guild.id, member.id, 0, 0))
                row = {"exp": 0, "level": 0}

            new_exp = row["exp"] + xp
            new_level = int((math.sqrt(1 + 8 * new_exp / config.LEVEL_DIVISOR) - 1) / 2)

            conn.execute("UPDATE glevel SET exp = ?, level = ? WHERE guild_id = ? AND user_id = ?",
                        (new_exp, new_level, member.guild.id, member.id))

            old_level = row["level"]

        if new_level > old_level:
            try:
                await member.send(f"GG {member.mention}! You reached **Level {new_level}** in **{member.guild.name}**!")
            except discord.Forbidden:
                logger.debug(f"Could not DM {member} about level up")

        # Auto-role
        with get_db() as conn:
            roles = conn.execute("SELECT role_id, level FROM ranks WHERE guild_id = ?", (member.guild.id,)).fetchall()
            for r in roles:
                if new_level >= r["level"]:
                    role = member.guild.get_role(r["role_id"])
                    if role and role not in member.roles:
                        try:
                            await member.add_roles(role, reason="Level reward")
                        except discord.Forbidden:
                            logger.warning(f"Cannot assign role {role.name} to {member} - missing permissions")

    # === TEXT XP ===
    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or message.author.bot:
            return

        with get_db() as conn:
            enabled = conn.execute("SELECT enabled FROM glevel WHERE guild_id = ?", (message.guild.id,)).fetchone()
            if not enabled or enabled["enabled"] != "enabled":
                return

        await self.give_xp(message.author, random.randint(config.TEXT_XP_MIN, config.TEXT_XP_MAX))
        await self.bot.process_commands(message)

    # === VOICE XP ===
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        # Cancel existing task if any (handles left, switched, or rejoined)
        if member.id in self.voice_tasks:
            old_task = self.voice_tasks.pop(member.id)
            if not old_task.done():
                old_task.cancel()
                try:
                    await old_task
                except asyncio.CancelledError:
                    pass

        # Joined or switched to a voice channel
        if after.channel:
            # Don't give XP if alone or only with bots
            if len(after.channel.members) <= 1:
                return
            if all(m.bot for m in after.channel.members if m.id != member.id):
                return

            async def voice_loop():
                try:
                    while True:
                        await asyncio.sleep(config.VOICE_XP_INTERVAL)
                        # Verify member is still in voice before giving XP
                        if member.voice and member.voice.channel:
                            # Re-check they're not alone
                            channel = member.voice.channel
                            if len(channel.members) > 1 and not all(m.bot for m in channel.members if m.id != member.id):
                                await self.give_xp(member, random.randint(config.VOICE_XP_MIN, config.VOICE_XP_MAX))
                        else:
                            # Member left voice, cancel task
                            break
                except asyncio.CancelledError:
                    logger.debug(f"Voice XP task cancelled for {member}")
                except Exception as e:
                    logger.error(f"Error in voice XP loop for {member}: {e}", exc_info=True)

            task = asyncio.create_task(voice_loop())
            self.voice_tasks[member.id] = task

async def setup(bot):
    await bot.add_cog(Leveling(bot))
