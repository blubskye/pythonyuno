from discord.ext import commands
import discord
import datetime

class Public(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["info", "botinfo", "about"])
    async def bot(self, ctx):
        embed = discord.Embed(title="Yuno Gasai • Reborn", color=0xff003d, timestamp=datetime.datetime.utcnow())
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.add_field(name="Servers", value=f"`{len(self.bot.guilds)}`", inline=True)
        embed.add_field(name="Users", value=f"`{len(self.bot.users)}`", inline=True)
        embed.add_field(name="Shards", value="`1`", inline=True)
        embed.add_field(name="Python", value="`3.11+`", inline=True)
        embed.add_field(name="discord.py", value=f"`{discord.__version__}`", inline=True)
        embed.add_field(name="Uptime", value="`Forever`", inline=True)
        embed.set_footer(text="AGPL-3.0 • Open Source • https://github.com/blubskye/pythonyuno")
        await ctx.send(embed=embed)

    @commands.command()
    async def invite(self, ctx):
        url = discord.utils.oauth_url(self.bot.user.id, permissions=discord.Permissions(8))
        embed = discord.Embed(title="Invite Yuno", description=f"[Click here to invite me]({url})", color=0xff003d)
        embed.set_footer(text="Thank you for choosing Yuno ♡")
        await ctx.send(embed=embed)

    @commands.command(name="source", aliases=["src", "code", "github"])
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def source(self, ctx):
        url = "https://github.com/blubskye/pythonyuno"
        embed = discord.Embed(
            title="Yuno • Open Source",
            description=f"This bot is licensed under **GNU AGPL-3.0**\n"
                        f"[View source code on GitHub]({url})",
            color=0xff003d,
            url=url
        )
        embed.set_thumbnail(url="https://www.gnu.org/graphics/agplv3-155x51.png")
        embed.set_footer(text="Free as in freedom • You own your instance")
        try:
            await ctx.author.send(embed=embed)
            await ctx.message.add_reaction("")
        except:
            await ctx.send(embed=embed)

    @commands.command()
    async def help(self, ctx):
        embed = discord.Embed(title="Yuno Commands • Help", color=0xff003d)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        embed.add_field(
            name="Leveling & Ranks",
            value="`?rank [@user]` • `?leaderboard`\n"
                  "`?ranks add/remove/list` • `?leveling on/off`",
            inline=False
        )
        embed.add_field(
            name="Moderation",
            value="`?ban @user` • `?unban ID` • `?clear 50`\n"
                  "`?setmyban` • `?setdefaultban`\n"
                  "`?exportbans` • `?importbans`",
            inline=False
        )
        embed.add_field(
            name="Fun & Social",
            value="`?neko` / `?neko lewd` • `?8ball`\n"
                  "`?quote` • `?quote add`\n"
                  "`?stats`",
            inline=False
        )
        embed.add_field(
            name="Server Management",
            value="`?setwelcome #channel` • `?welcomemode both`\n"
                  "`?welcomemsg Welcome {member}!`\n"
                  "`?welcomeimage` • `?welcome on/off`",
            inline=False
        )
        embed.add_field(
            name="Utility",
            value="`?ping` • `?invite` • `?source`",
            inline=False
        )
        embed.add_field(
            name="Owner Only",
            value="`?terminal` • `?restart` • `?py`",
            inline=False
        )

        embed.set_footer(text="Mention me for a surprise • Ara~")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Public(bot))
    print("Public commands loaded — help, source, info, invite ready.")
