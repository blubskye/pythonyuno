from discord.ext import commands

def is_mod():
    async def pred(ctx):
        return ctx.author.guild_permissions.manage_messages or await ctx.bot.is_owner(ctx.author)
    return commands.check(pred)

def is_admin():
    async def pred(ctx):
        return ctx.author.guild_permissions.administrator or await ctx.bot.is_owner(ctx.author)
    return commands.check(pred)
