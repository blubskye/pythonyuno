import discord
from discord.ext import commands
import re
from collections import defaultdict, deque
import asyncio

# === CONFIGURABLE RULES ===
INVITE_REGEX = re.compile(r"(discord\.(gg|io|me|li)|discordapp\.com/invite)/[a-zA-Z0-9]+")
LINK_REGEX = re.compile(r"(https?://|www\.)[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-\._~:\/\?#\[\]@!\$&'\(\)\*\+,;=%]+")

class SpamFilter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Per-user warning tracking
        self.link_warnings = set()           # Users warned for links in #main
        self.nsfw_text_warnings = set()      # Users warned in nsfw_* channels
        self.spam_streak = defaultdict(int)  # Consecutive messages in main

        # Message history per channel (last 10 messages)
        self.recent_messages = defaultdict(lambda: deque(maxlen=10))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        # Cache member if needed
        if message.author.id not in message.guild.members:
            try:
                await message.guild.fetch_member(message.author.id)
            except:
                return

        # Skip mods/admins
        if message.author.guild_permissions.manage_messages:
            return await self.bot.process_commands(message)

        content = message.content
        channel_name = message.channel.name.lower()

        # Store in recent history
        self.recent_messages[message.channel.id].append(message)

        # === RULE 1: Discord invites → instant ban ===
        if INVITE_REGEX.search(content):
            return await self.auto_ban(message, "Posted Discord invite link")

        # === RULE 2: NSFW channels (nsfw_*) — no text, only links/images ===
        if channel_name.startswith("nsfw_"):
            has_link = bool(LINK_REGEX.search(content)) or message.attachments
            if content.strip() and not has_link:
                if message.author.id in self.nsfw_text_warnings:
                    self.nsfw_text_warnings.remove(message.author.id)
                    return await self.auto_ban(message, "Text in NSFW image-only channel (2nd offense)")
                else:
                    self.nsfw_text_warnings.add(message.author.id)
                    await message.delete()
                    try:
                        await message.author.send(
                            "Text is not allowed in NSFW image channels (like this one).\n"
                            "Only links and images are permitted to reduce clutter.\n"
                            "Please discuss in #main-chat or #media instead."
                        )
                    except:
                        pass
                    return

        # === RULE 3: @everyone / @here → instant ban ===
        if "@everyone" in content or "@here" in content:
            if message.author.guild_permissions.mention_everyone:
                pass  # Allowed if they have permission
            else:
                return await self.auto_ban(message, "Unauthorized @everyone or @here")

        # === RULE 4: Links in #main → one warning, then ban ===
        if channel_name.startswith("main"):
            if LINK_REGEX.search(content):
                if message.author.id in self.link_warnings:
                    self.link_warnings.remove(message.author.id)
                    return await self.auto_ban(message, "Posted link in #main after warning")
                else:
                    self.link_warnings.add(message.author.id)
                    await message.delete()
                    warning = await message.channel.send(
                        f"{message.author.mention} Links are not allowed in main chat. This is your **only warning**.\n"
                        "Next offense = ban."
                    )
                    await asyncio.sleep(15)
                    await warning.delete()
                    return

            # === RULE 5: 4+ consecutive messages in #main → warning, then ban ===
            recent = self.recent_messages[message.channel.id]
            if len(recent) >= 4:
                authors = [m.author.id for m in list(recent)[-4:]]
                if all(a == message.author.id for a in authors):
                    if message.author.id in self.spam_streak:
                        self.spam_streak.pop(message.author.id, None)
                        return await self.auto_ban(message, "Message spam (4+ consecutive in main)")
                    else:
                        self.spam_streak[message.author.id] = True
                        warning = await message.channel.send(
                            f"{message.author.mention} Please keep messages under 4 in a row in main chat.\n"
                            "This is your **only warning**. Next burst = ban."
                        )
                        await asyncio.sleep(15)
                        await warning.delete()

        await self.bot.process_commands(message)

    async def auto_ban(self, message: discord.Message, reason: str):
        try:
            await message.author.send(
                f"You have been **banned** from **{message.guild.name}**\n"
                f"Reason: `{reason}`\n"
                "This action was automatic. Contact staff if you believe this was a mistake."
            )
        except:
            pass

        try:
            await message.author.ban(reason=f"[Auto] {reason}", delete_message_seconds=86400)
            await message.channel.send(f"{message.author.mention} has been auto-banned: {reason}")
        except discord.Forbidden:
            await message.channel.send("I don't have permission to ban this user.")
        except Exception as e:
            print(f"Failed to ban {message.author}: {e}")

async def setup(bot):
    await bot.add_cog(SpamFilter(bot))
    print("Advanced spam filter loaded — Yuno is watching.")
