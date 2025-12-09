import discord
from discord.ext import commands
import random
import os

RESPONSES_FOLDER = "mention_responses"
os.makedirs(RESPONSES_FOLDER, exist_ok=True)

class Mention(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.text_responses = [
            "Ara ara~",
            "Yes, master?",
            "Hehe~",
            "I'm here!",
            "You called? ♡",
            "Yuno is watching...",
            "Good job~",
            "I'm proud of you!",
            "Keep going, ara~"
        ]

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # Direct mention (or reply to bot)
        if self.bot.user in message.mentions or (message.reference and message.reference.resolved and message.reference.resolved.author == self.bot.user):
            # 60% chance to respond
            if random.random() < 0.6:
                # Try to send image first
                images = [f for f in os.listdir(RESPONSES_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
                if images:
                    img = random.choice(images)
                    file = discord.File(f"{RESPONSES_FOLDER}/{img}", filename="yuno.png")
                    await message.reply(file=file, mention_author=False)
                else:
                    # Fallback to text
                    response = random.choice(self.text_responses)
                    await message.reply(response, mention_author=False)

        await self.bot.process_commands(message)

async def setup(bot):
    await bot.add_cog(Mention(bot))
    print("Mention responses loaded — Yuno hears you ♡")
