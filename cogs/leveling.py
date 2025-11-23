import discord
from discord.ext import commands
import sqlite3
import datetime
import math
import random
import asyncio
from utils.checks import is_admin

DB_PATH = "Leveling/main.db"

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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

            conn = db()
            conn.execute("INSERT OR REPLACE INTO ranks(guild_id, role_id, level) VALUES(?, ?, ?)",
                        (ctx.guild.id, role.id, level))
            conn.commit()
            conn.close()
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

        conn = db()
        conn.execute("DELETE FROM ranks WHERE guild_id = ? AND role_id = ?", (ctx.guild.id, role.id))
        conn.commit()
        conn.close()
        await ctx.send("Removed.")

    @ranks.command(name="list")
    async def _list(self, ctx):
        conn = db()
        rows = conn.execute("SELECT role_id, level FROM ranks WHERE guild_id = ?", (ctx.guild.id,)).fetchall()
        if not rows:
            return await ctx.send("No ranks set.")
        text = "\n".join(f"<@&{r['role_id']}> → Level {r['level']}" for r in rows)
        await ctx.send(text)
        conn.close()

    # === LEVELING TOGGLE ===
    @commands.group()
    async def leveling(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("`?leveling enable` / `?leveling disable`")

    @leveling.command()
    @is_admin()
    async def enable(self, ctx):
        conn = db()
        conn.execute("INSERT OR REPLACE INTO glevel(guild_id, enabled) VALUES(?, 'enabled')", (ctx.guild.id,))
        conn.commit()
        conn.close()
        await ctx.send("Leveling enabled.")

    @leveling.command()
    @is_admin()
    async def disable(self, ctx):
        conn = db()
        conn.execute("INSERT OR REPLACE INTO glevel(guild_id, enabled) VALUES(?, 'disabled')", (ctx.guild.id,))
        conn.commit()
        conn.close()
        await ctx.send("Leveling disabled.")

    # === CORE XP ===
    async def give_xp(self, member: discord.Member, xp: int):
        if member.bot: return
        conn = db()
        row = conn.execute("SELECT exp, level FROM glevel WHERE guild_id = ? AND user_id = ?",
                          (member.guild.id, member.id)).fetchone()
        if not row:
            conn.execute("INSERT INTO glevel(guild_id, user_id, exp, level) VALUES(?, ?, ?, ?)",
                        (member.guild.id, member.id, 0, 0))
            conn.commit()
            row = {"exp": 0, "level": 0}

        new_exp = row["exp"] + xp
        new_level = int((math.sqrt(1 + 8 * new_exp / 50) - 1) / 2)

        conn.execute("UPDATE glevel SET exp = ?, level = ? WHERE guild_id = ? AND user_id = ?",
                    (new_exp, new_level, member.guild.id, member.id))
        conn.commit()
        conn.close()

        if new_level > row["level"]:
            await member.send(f"GG {member.mention}! You reached **Level {new_level}** in **{member.guild.name}**!")

        # Auto-role
        conn = db()
        roles = conn.execute("SELECT role_id, level FROM ranks WHERE guild_id = ?", (member.guild.id,)).fetchall()
        for r in roles:
            if new_level >= r["level"]:
                role = member.guild.get_role(r["role_id"])
                if role and role not in member.roles:
                    await member.add_roles(role, reason="Level reward")
        conn.close()

    # === TEXT XP ===
    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or message.author.bot:
            return
        conn = db()
        enabled = conn.execute("SELECT enabled FROM glevel WHERE guild_id = ?", (message.guild.id,)).fetchone()
        if not enabled or enabled["enabled"] != "enabled":
            return conn.close()

        await self.give_xp(message.author, random.randint(15, 25))
        conn.close()

        await self.bot.process_commands(message)

    # === VOICE XP ===
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot: return

        # Left voice
        if before.channel and not after.channel:
            task = self.voice_tasks.get(member.id)
            if task: task.cancel()

        # Joined voice
        if after.channel and after.channel != before.channel:
            if not after.channel.members: return
            if any(m.bot for m in after.channel.members): return

            async def voice_loop():
                while True:
                    await asyncio.sleep(60)
                    if member.voice and member.voice.channel == after.channel:
                        await self.give_xp(member, random.randint(18, 30))

            task = asyncio.create_task(voice_loop())
            self.voice_tasks[member.id] = task

async def setup(bot):
    await bot.add_cog(Leveling(bot))
