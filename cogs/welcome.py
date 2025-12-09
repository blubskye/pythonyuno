import discord
from discord.ext import commands
import sqlite3
import logging
import config

logger = logging.getLogger(__name__)

DB_PATH = config.DB_PATH

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.create_table()

    def create_table(self):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS welcome (
                guild_id INTEGER PRIMARY KEY,
                channel_id INTEGER,
                dm_enabled INTEGER DEFAULT 0,
                channel_enabled INTEGER DEFAULT 1,
                message TEXT DEFAULT 'Welcome {member} to {guild}!',
                embed_color INTEGER DEFAULT 16761035,
                image_url TEXT,
                enabled INTEGER DEFAULT 1
            )
        """)
        conn.commit()
        conn.close()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            return

        conn = sqlite3.connect(DB_PATH)
        row = conn.execute(
            "SELECT channel_id, dm_enabled, channel_enabled, message, embed_color, image_url, enabled FROM welcome WHERE guild_id = ?",
            (member.guild.id,)
        ).fetchone()
        conn.close()

        if not row or not row[6]:  # enabled == 0
            return

        channel_id, dm_on, chan_on, raw_msg, color, image_url, _ = row
        channel = member.guild.get_channel(channel_id) if channel_id else None

        # Replace placeholders
        message = raw_msg.replace("{member}", member.mention) \
                         .replace("{user}", str(member)) \
                         .replace("{guild}", member.guild.name) \
                         .replace("{count}", str(member.guild.member_count))

        embed = discord.Embed(description=message, color=color or 0xff003d)
        embed.set_author(name=f"Welcome {member}!", icon_url=member.display_avatar.url)
        embed.set_footer(text=f"Member #{member.guild.member_count}")
        if image_url:
            embed.set_image(url=image_url)

        # === SEND TO CHANNEL ===
        if chan_on and channel:
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                logger.warning(f"Cannot send welcome to {channel.id} - missing permissions")
            except discord.HTTPException as e:
                logger.error(f"Failed to send welcome message: {e}")

        # === SEND TO DM ===
        if dm_on:
            try:
                await member.send(embed=embed)
            except discord.Forbidden:
                logger.debug(f"Cannot DM {member.id} - DMs are closed")
                # Optional: notify in channel that DM failed
                if chan_on and channel:
                    try:
                        await channel.send(f"{member.mention} I tried to DM you a welcome, but your privacy settings block it!")
                    except discord.HTTPException as e:
                        logger.error(f"Failed to notify about DM failure: {e}")

    # === SET WELCOME CHANNEL ===
    @commands.command(name="setwelcome")
    @commands.has_permissions(manage_guild=True)
    async def set_channel(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT OR REPLACE INTO welcome (guild_id, channel_id, channel_enabled) VALUES (?, ?, 1)",
            (ctx.guild.id, channel.id)
        )
        conn.commit()
        conn.close()
        await ctx.send(f"Welcome channel set to {channel.mention}")

    # === TOGGLE DM / CHANNEL / BOTH ===
    @commands.command(name="welcomemode")
    @commands.has_permissions(manage_guild=True)
    async def set_mode(self, ctx, mode: str):
        mode = mode.lower()
        if mode not in ["dm", "channel", "both"]:
            return await ctx.send("Usage: `?welcomemode dm` | `channel` | `both`")

        conn = sqlite3.connect(DB_PATH)
        dm = 1 if mode in ["dm", "both"] else 0
        chan = 1 if mode in ["channel", "both"] else 0

        conn.execute(
            "INSERT OR REPLACE INTO welcome (guild_id, dm_enabled, channel_enabled) VALUES (?, ?, ?)",
            (ctx.guild.id, dm, chan)
        )
        conn.commit()
        conn.close()

        status = "DMs only" if mode == "dm" else "Channel only" if mode == "channel" else "Both DM + Channel"
        await ctx.send(f"Welcome delivery mode: **{status}**")

    # === CUSTOMIZE MESSAGE ===
    @commands.command(name="welcomemsg")
    @commands.has_permissions(manage_guild=True)
    async def set_message(self, ctx, *, text: str):
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "UPDATE welcome SET message = ? WHERE guild_id = ?",
            (text, ctx.guild.id)
        )
        if conn.rowcount == 0:
            conn.execute(
                "INSERT INTO welcome (guild_id, message, enabled) VALUES (?, ?, 1)",
                (ctx.guild.id, text)
            )
        conn.commit()
        conn.close()

        preview = text.replace("{member}", ctx.author.mention) \
                     .replace("{user}", str(ctx.author)) \
                     .replace("{guild}", ctx.guild.name) \
                     .replace("{count}", "1234")

        embed = discord.Embed(title="Welcome message updated!", description=preview, color=0xff003d)
        embed.set_footer(text="Placeholders: {member}, {user}, {guild}, {count}")
        await ctx.send(embed=embed)

    # === SET IMAGE ===
    @commands.command(name="welcomeimage")
    @commands.has_permissions(manage_guild=True)
    async def set_image(self, ctx):
        if not ctx.message.attachments and len(ctx.message.content.split()) < 2:
            return await ctx.send("Attach an image or provide a URL.")

        url = ctx.message.attachments[0].url if ctx.message.attachments else ctx.message.content.split()[1]

        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "UPDATE welcome SET image_url = ? WHERE guild_id = ?",
            (url, ctx.guild.id)
        )
        if conn.rowcount == 0:
            conn.execute("INSERT INTO welcome (guild_id, image_url) VALUES (?, ?)", (ctx.guild.id, url))
        conn.commit()
        conn.close()

        embed = discord.Embed(title="Welcome image updated!", color=0xff003d)
        embed.set_image(url=url)
        await ctx.send(embed=embed)

    # === MASTER TOGGLE ===
    @commands.command(name="welcome")
    @commands.has_permissions(manage_guild=True)
    async def toggle(self, ctx, state: str = None):
        if state and state.lower() not in ["on", "off"]:
            return await ctx.send("Usage: `?welcome on` | `off`")

        conn = sqlite3.connect(DB_PATH)
        if state:
            enabled = 1 if state.lower() == "on" else 0
            conn.execute("INSERT OR REPLACE INTO welcome (guild_id, enabled) VALUES (?, ?)", (ctx.guild.id, enabled))
            status = "enabled" if enabled else "disabled"
        else:
            row = conn.execute("SELECT enabled FROM welcome WHERE guild_id = ?", (ctx.guild.id,)).fetchone()
            status = "currently ON" if row and row[0] else "currently OFF"
        conn.commit()
        conn.close()
        await ctx.send(f"Welcome system {status}")

async def setup(bot):
    await bot.add_cog(Welcome(bot))
    logger.info("Advanced welcome system loaded — DM + Channel + Both ♡")
