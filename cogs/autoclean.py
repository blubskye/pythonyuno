import discord
from discord.ext import commands, tasks
import sqlite3
import asyncio
from datetime import datetime, timedelta

DB_PATH = "Leveling/main.db"

class AutoClean(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.autoclean_loop.start()

    def cog_unload(self):
        self.autoclean_loop.cancel()

    def get_db(self):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS autoclean (
                guild_id INTEGER,
                channel_id INTEGER,
                interval_hours INTEGER,
                warning_minutes INTEGER,
                next_run TEXT,
                PRIMARY KEY (guild_id, channel_id)
            )
        """)
        return conn

    @commands.command(name="autoclean")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def autoclean(self, ctx, interval_hours: int, warning_minutes: int = 5, channel: discord.TextChannel = None):
        """
        .autoclean 24 5 #general → cleans #general every 24h with 5min warning
        """
        if interval_hours < 1:
            return await ctx.send("Interval must be at least 1 hour.")
        if warning_minutes < 1 or warning_minutes > 60:
            return await ctx.send("Warning must be 1–60 minutes.")

        channel = channel or ctx.channel

        # Save schedule
        conn = self.get_db()
        next_run = datetime.utcnow() + timedelta(hours=interval_hours)
        conn.execute("""
            INSERT OR REPLACE INTO autoclean 
            (guild_id, channel_id, interval_hours, warning_minutes, next_run)
            VALUES (?, ?, ?, ?, ?)
        """, (ctx.guild.id, channel.id, interval_hours, warning_minutes, next_run.isoformat()))
        conn.commit()
        conn.close()

        await ctx.send(
            f"Auto-clean scheduled for {channel.mention}\n"
            f"Every **{interval_hours}h** | Warning: **{warning_minutes} min** before reset\n"
            f"Next clean: <t:{int(next_run.timestamp())}:R>"
        )

    @commands.command(name="autoclean-stop")
    @commands.has_permissions(manage_channels=True)
    async def stop_autoclean(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        conn = self.get_db()
        cur = conn.execute("DELETE FROM autoclean WHERE guild_id = ? AND channel_id = ?", (ctx.guild.id, channel.id))
        conn.commit()
        conn.close()

        if cur.rowcount:
            await ctx.send(f"Stopped auto-clean for {channel.mention}")
        else:
            await ctx.send("No active auto-clean found for this channel.")

    @tasks.loop(minutes=1)
    async def autoclean_loop(self):
        now = datetime.utcnow()
        conn = self.get_db()
        rows = conn.execute("SELECT * FROM autoclean").fetchall()
        for row in rows:
            next_run = datetime.fromisoformat(row["next_run"])
            if now >= next_run:
                channel = self.bot.get_channel(row["channel_id"])
                if not channel:
                    continue

                warning_min = row["warning_minutes"]
                interval_h = row["interval_hours"]

                # Send warning
                warning_msg = await channel.send(
                    f"**Channel will be cleaned in {warning_min} minute(s)!**\n"
                    "Last chance to save anything important."
                )
                await asyncio.sleep(warning_min * 60)

                # Clone & delete
                try:
                    new_channel = await channel.clone(reason="Auto-clean scheduled")
                    await new_channel.edit(position=channel.position, reason="Preserve position")
                    await channel.delete(reason="Auto-clean")
                    await new_channel.send(
                        f"Channel cleaned! Next clean in **{interval_h} hour(s)**\n"
                        f"Previous messages are gone — this is a fresh start."
                    )
                except discord.Forbidden:
                    await warning_msg.edit(content="Auto-clean failed: Missing permissions.")
                except Exception as e:
                    await warning_msg.edit(content=f"Auto-clean failed: {e}")

                # Reschedule
                next_run = datetime.utcnow() + timedelta(hours=interval_h)
                conn.execute(
                    "UPDATE autoclean SET next_run = ? WHERE guild_id = ? AND channel_id = ?",
                    (next_run.isoformat(), row["guild_id"], row["channel_id"])
                )
                conn.commit()

        conn.close()

    @autoclean_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(AutoClean(bot))
