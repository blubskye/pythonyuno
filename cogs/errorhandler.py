import discord
from discord.ext import commands
import traceback
import textwrap
from utils.checks import is_admin  # optional, or use is_owner

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tracing_enabled = False
        self.log_channel_id = None  # Set with .settracechannel

        # Replace default handler
        bot.tree.on_error = self.on_app_command_error
        self.bot.add_listener(self.on_command_error, "on_command_error")

    def cog_unload(self):
        self.bot.tree.on_error = lambda *args: None

    # === TOGGLE TRACING ===
    @commands.command(name="trace")
    @commands.is_owner()
    async def toggle_trace(self, ctx):
        self.tracing_enabled = not self.tracing_enabled
        status = "ON" if self.tracing_enabled else "OFF"
        await ctx.send(f"Full-stack tracing is now **{status}**")

    @commands.command(name="settracechannel")
    @commands.is_owner()
    async def set_trace_channel(self, ctx, channel: discord.TextChannel = None):
        if not channel:
            channel = ctx.channel
        self.log_channel_id = channel.id
        await ctx.send(f"Traceback logs will be sent to {channel.mention}")

    # === GLOBAL ERROR CATCHER ===
    async def send_traceback(self, error, ctx=None, interaction=None):
        if not self.tracing_enabled or not self.log_channel_id:
            return

        channel = self.bot.get_channel(self.log_channel_id)
        if not channel:
            return

        tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        lines = tb.strip().split('\n')
        formatted = f"```py\n{tb[-1900:]}\n```"  # Discord limit ~2000 chars

        embed = discord.Embed(title="Full Exception Traceback", color=0xff0000, timestamp=discord.utils.utcnow())
        embed.add_field(name="Error", value=f"`{type(error).__name__}: {error}`", inline=False)
        if ctx:
            embed.add_field(name="Command", value=ctx.command.qualified_name if ctx.command else "None", inline=True)
            embed.add_field(name="User", value=f"{ctx.author} ({ctx.author.id})", inline=True)
            embed.add_field(name="Channel", value=ctx.channel.mention, inline=True)
        if interaction:
            embed.add_field(name="Slash Command", value=interaction.command.name, inline=True)
            embed.add_field(name="User", value=f"{interaction.user} ({interaction.user.id})", inline=True)

        embed.add_field(name="Traceback", value=formatted, inline=False)
        embed.set_footer(text=f"Guild: {ctx.guild.name if ctx and ctx.guild else interaction.guild.name if interaction and interaction.guild else 'DM'}")

        try:
            await channel.send(embed=embed)
        except:
            pass  # Silent fail if log channel is invalid

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, (commands.CommandNotFound, commands.NotOwner)):
            return

        await self.send_traceback(error, ctx=ctx)

        # Optional: still show user-friendly message
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command.")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("I don't have permission to do that.")
        else:
            await ctx.send(f"An error occurred: `{error}`")

    async def on_app_command_error(self, interaction: discord.Interaction, error):
        await self.send_traceback(error, interaction=interaction)

        try:
            if interaction.response.is_done():
                await interaction.followup.send("An error occurred while processing the command.", ephemeral=True)
            else:
                await interaction.response.send_message("An error occurred.", ephemeral=True)
        except:
            pass

async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))
