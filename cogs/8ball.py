import discord
from discord.ext import commands
import sqlite3
import random

DB_PATH = "Leveling/main.db"

class Quotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.create_table()

    def create_table(self):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                content TEXT,
                author_id INTEGER,
                added_by INTEGER
            )
        """)
        conn.commit()
        conn.close()

    @commands.group(invoke_without_command=True)
    async def quote(self, ctx):
        """Get a random quote"""
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute(
            "SELECT content, author_id FROM quotes WHERE guild_id = ? ORDER BY RANDOM() LIMIT 1",
            (ctx.guild.id,)
        ).fetchone()
        conn.close()

        if not row:
            return await ctx.send("No quotes yet. Use `?quote add <text>` to add one!")

        content, author_id = row
        author = self.bot.get_user(author_id) or "Unknown User"
        embed = discord.Embed(description=f"\"{content}\"", color=0xff003d)
        embed.set_footer(text=f"— {author}")
        await ctx.send(embed=embed)

    @quote.command(name="add")
    @commands.has_permissions(manage_messages=True)
    async def add_quote(self, ctx, *, text: str):
        """Add a new quote"""
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT INTO quotes (guild_id, content, author_id, added_by) VALUES (?, ?, ?, ?)",
            (ctx.guild.id, text.strip(), ctx.author.id, ctx.author.id)
        )
        conn.commit()
        conn.close()
        await ctx.send(f"Quote added! Total: {self.count_quotes(ctx.guild.id)}")

    @quote.command(name="list")
    async def list_quotes(self, ctx):
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute(
            "SELECT id, content FROM quotes WHERE guild_id = ?",
            (ctx.guild.id,)
        ).fetchall()
        conn.close()

        if not rows:
            return await ctx.send("No quotes.")

        lines = [f"`{r[0]}` {r[1][:80]}{'...' if len(r[1]) > 80 else ''}" for r in rows]
        pages = [lines[i:i+15] for i in range(0, len(lines), 15)]
        for i, page in enumerate(pages, 1):
            embed = discord.Embed(title=f"Quotes ({i}/{len(pages)})", description="\n".join(page), color=0xff003d)
            await ctx.send(embed=embed)

    def count_quotes(self, guild_id):
        conn = sqlite3.connect(DB_PATH)
        count = conn.execute("SELECT COUNT(*) FROM quotes WHERE guild_id = ?", (guild_id,)).fetchone()[0]
        conn.close()
        return count

async def setup(bot):
    await bot.add_cog(Quotes(bot))
    print("Quotes system loaded — wisdom preserved.")
