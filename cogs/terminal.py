import discord
from discord.ext import commands
import asyncio
import subprocess
import textwrap
import os
import sys
import traceback
import logging
from contextlib import redirect_stdout
import io
import config

logger = logging.getLogger(__name__)

class Terminal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sessions = {}  # user_id → active session

    async def _run_command(self, code: str, ctx):
        if code.strip().startswith("```"):
            code = "\n".join(code.strip().split("\n")[1:-1])

        env = {
            'bot': self.bot,
            'discord': discord,
            'commands': commands,
            'ctx': ctx,
            '__import__': __import__
        }

        stdout = io.StringIO()
        try:
            with redirect_stdout(stdout):
                # Detect shell command (starts with !)
                if code.strip().startswith("!"):
                    cmd = code[1:].strip()
                    proc = await asyncio.create_subprocess_shell(
                        cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout_data, stderr_data = await proc.communicate()
                    output = (stdout_data or b"").decode() + (stderr_data or b"").decode()
                else:
                    # Python code
                    exec(f"async def func():\n{textwrap.indent(code, '    ')}", env)
                    await eval("func()", env)
                    output = stdout.getvalue()
        except Exception as e:
            output = "".join(traceback.format_exception(type(e), e, e.__traceback__))

        return output or "No output."

    @commands.command(name="terminal", aliases=["term", "shell", ">"])
    @commands.is_owner()
    async def terminal(self, ctx, *, code: str = None):
        """Owner-only live terminal"""
        if not code:
            return await ctx.send("```css\nYuno Terminal v2 — type code or !command\nExample: !git pull\n         print('hello')\n```")

        # Run the command
        async with ctx.typing():
            result = await self._run_command(code, ctx)

        # Split long output
        pages = [result[i:i+1990] for i in range(0, len(result), 1990)]
        for i, page in enumerate(pages):
            prefix = f"Output {i+1}/{len(pages)}:\n" if len(pages) > 1 else "Output:\n"
            await ctx.send(f"```{'' if page.strip() else 'css'}\n{prefix}{page}\n```")

    # Bonus: persistent shell with history
    @commands.command(name="py")
    @commands.is_owner()
    async def python_shell(self, ctx):
        """Interactive Python REPL"""
        if ctx.author.id in self.sessions:
            return await ctx.send("You already have a session running.")

        await ctx.send("**Yuno Interactive Python Shell**\nType `exit()` or `quit()` to close.\n```py\n>>> ```")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        session = {"history": []}
        self.sessions[ctx.author.id] = session

        while True:
            try:
                msg = await self.bot.wait_for("message", check=check, timeout=config.TERMINAL_SESSION_TIMEOUT)
            except asyncio.TimeoutError:
                del self.sessions[ctx.author.id]
                return await ctx.send("Terminal timed out.")

            if msg.content.lower() in ["exit()", "quit()", "exit", "quit"]:
                del self.sessions[ctx.author.id]
                return await ctx.send("Terminal closed.")

            result = await self._run_command(msg.content, ctx)
            session["history"].append((msg.content, result))

            if len(result) > 1900:
                result = result[:1890] + "\n... (truncated)"
            await ctx.send(f"```py\n{result}\n```")

    # Quick restart
    @commands.command(name="restart")
    @commands.is_owner()
    async def restart_bot(self, ctx):
        await ctx.send("Restarting Yuno...")
        os.execv(sys.executable, ['python'] + sys.argv)

async def setup(bot):
    await bot.add_cog(Terminal(bot))
    logger.info("Interactive terminal loaded — full system access granted.")
