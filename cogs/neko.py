import discord
from discord.ext import commands
import aiohttp
import random

NEKO_API = "https://nekos.life/api/v2/img/neko"
LEWD_NEKO_API = "https://nekos.life/api/v2/img/lewdneko"

class Neko(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    async def _get_neko(self, url: str):
        async with self.session.get(url) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            return data.get("url")

    @commands.command(name="neko", aliases=["nya", "catgirl"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def neko(self, ctx, mode: str = "sfw"):
        """Get a cute neko~ (use 'lewd' in NSFW channels)"""
        mode = mode.lower()

        if mode in ["lewd", "l", "nsfw"]:
            if not ctx.channel.is_nsfw():
                return await ctx.send("Ara ara~ I can only show lewd nekos in NSFW channels!")
            url = LEWD_NEKO_API
            color = 0xff69b4  # hot pink
        else:
            url = NEKO_API
            color = 0xff003d  # Yuno red

        await ctx.trigger_typing()

        image_url = await self._get_neko(url)
        if not image_url:
            return await ctx.send("Nya~ The neko ran away... try again!")

        embed = discord.Embed(color=color)
        embed.set_image(url=image_url)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

    async def cog_unload(self):
        await self.session.close()

async def setup(bot):
    await bot.add_cog(Neko(bot))
    print("Neko command loaded — nya~ ♡")
