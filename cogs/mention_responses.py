import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import random
import os
import logging
from contextlib import contextmanager
from cogs.utils.checks import is_admin
import config

DB_PATH = config.DB_PATH
RESPONSES_FOLDER = "mention_responses"
logger = logging.getLogger(__name__)

os.makedirs(RESPONSES_FOLDER, exist_ok=True)

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}", exc_info=True)
        raise
    finally:
        conn.close()

def init_mention_tables():
    """Initialize mention response tables"""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mention_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                trigger TEXT NOT NULL,
                response TEXT,
                image_path TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, trigger)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_mention_guild ON mention_responses(guild_id)
        """)

class MentionResponses(commands.Cog):
    """Custom mention-based auto responses"""

    def __init__(self, bot):
        self.bot = bot
        self.default_responses = [
            "Ara ara~",
            "Yes, master?",
            "Hehe~",
            "I'm here!",
            "You called?",
            "Yuno is watching...",
            "Good job~",
            "I'm proud of you!",
            "Keep going, ara~"
        ]
        init_mention_tables()

    def get_response(self, guild_id: int, trigger: str = None):
        """Get a response for the guild, optionally matching a trigger"""
        with get_db() as conn:
            if trigger:
                row = conn.execute("""
                    SELECT response, image_path FROM mention_responses
                    WHERE guild_id = ? AND LOWER(trigger) = LOWER(?)
                """, (guild_id, trigger)).fetchone()
                if row:
                    return dict(row)

            # Get random guild response
            rows = conn.execute("""
                SELECT response, image_path FROM mention_responses WHERE guild_id = ?
            """, (guild_id,)).fetchall()
            if rows:
                return dict(random.choice(rows))

        return None

    # === ADD MENTION RESPONSE ===
    @commands.command(name="add-mentionresponse", aliases=["addmention", "addresponse"])
    @is_admin()
    async def add_mention_response(self, ctx, trigger: str, *, response: str = None):
        """Add a custom mention response

        Usage:
        ?add-mentionresponse "hello" "Hello there!"
        ?add-mentionresponse "pic" (attach image)
        """
        image_path = None

        # Check for attachment
        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            if attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                filename = f"{ctx.guild.id}_{trigger.replace(' ', '_')}_{attachment.filename}"
                image_path = os.path.join(RESPONSES_FOLDER, filename)
                await attachment.save(image_path)

        if not response and not image_path:
            return await ctx.send("Please provide a response text or attach an image.")

        with get_db() as conn:
            conn.execute("""
                INSERT INTO mention_responses (guild_id, trigger, response, image_path, created_by)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(guild_id, trigger) DO UPDATE SET
                    response = ?, image_path = ?, created_by = ?
            """, (ctx.guild.id, trigger.lower(), response, image_path, ctx.author.id,
                  response, image_path, ctx.author.id))

        embed = discord.Embed(
            title="Mention Response Added",
            color=config.COLOR_SUCCESS
        )
        embed.add_field(name="Trigger", value=f"`{trigger}`", inline=True)
        if response:
            embed.add_field(name="Response", value=response[:1024], inline=False)
        if image_path:
            embed.add_field(name="Image", value="Attached", inline=True)
        await ctx.send(embed=embed)

    # === DELETE MENTION RESPONSE ===
    @commands.command(name="del-mentionresponse", aliases=["delmention", "delresponse", "removemention"])
    @is_admin()
    async def del_mention_response(self, ctx, *, trigger: str):
        """Delete a custom mention response"""
        with get_db() as conn:
            # Get image path before deleting to clean up file
            row = conn.execute("""
                SELECT image_path FROM mention_responses
                WHERE guild_id = ? AND LOWER(trigger) = LOWER(?)
            """, (ctx.guild.id, trigger)).fetchone()

            if not row:
                return await ctx.send(f"No response found for trigger `{trigger}`")

            # Delete the record
            conn.execute("""
                DELETE FROM mention_responses
                WHERE guild_id = ? AND LOWER(trigger) = LOWER(?)
            """, (ctx.guild.id, trigger))

            # Clean up image file
            if row['image_path'] and os.path.exists(row['image_path']):
                try:
                    os.remove(row['image_path'])
                except OSError:
                    pass

        embed = discord.Embed(
            title="Mention Response Deleted",
            description=f"Removed response for trigger `{trigger}`",
            color=config.COLOR_WARNING
        )
        await ctx.send(embed=embed)

    # === LIST MENTION RESPONSES ===
    @commands.command(name="mentionresponses", aliases=["listmentions", "responses"])
    async def list_mention_responses(self, ctx):
        """List all custom mention responses for this server"""
        with get_db() as conn:
            rows = conn.execute("""
                SELECT id, trigger, response, image_path, created_by FROM mention_responses
                WHERE guild_id = ? ORDER BY trigger
            """, (ctx.guild.id,)).fetchall()

        if not rows:
            embed = discord.Embed(
                title="Mention Responses",
                description="No custom responses set for this server.\nUse `?add-mentionresponse <trigger> <response>` to add one.",
                color=config.COLOR_INFO
            )
            return await ctx.send(embed=embed)

        embed = discord.Embed(
            title=f"Mention Responses for {ctx.guild.name}",
            color=config.COLOR_INFO
        )

        for row in rows[:25]:  # Discord embed field limit
            value_parts = []
            if row['response']:
                value_parts.append(row['response'][:100] + ("..." if len(row['response']) > 100 else ""))
            if row['image_path']:
                value_parts.append("[Has Image]")

            embed.add_field(
                name=f"`{row['trigger']}`",
                value=" | ".join(value_parts) if value_parts else "Empty",
                inline=False
            )

        if len(rows) > 25:
            embed.set_footer(text=f"Showing 25/{len(rows)} responses")

        await ctx.send(embed=embed)

    # === MESSAGE LISTENER ===
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # Check if bot is mentioned
        if self.bot.user not in message.mentions:
            # Also check for reply to bot
            if not (message.reference and message.reference.resolved and
                    message.reference.resolved.author == self.bot.user):
                return

        # Extract potential trigger from message
        content = message.content.replace(f"<@{self.bot.user.id}>", "").replace(f"<@!{self.bot.user.id}>", "").strip().lower()

        # Try to find a matching trigger response
        response_data = None
        if content:
            response_data = self.get_response(message.guild.id, content)

        # If no specific match, get random guild response
        if not response_data:
            response_data = self.get_response(message.guild.id)

        # If still no response, use defaults
        if not response_data:
            # 60% chance to respond with default
            if random.random() < 0.6:
                # Try images from folder first
                images = [f for f in os.listdir(RESPONSES_FOLDER)
                         if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))
                         and not f.startswith(str(message.guild.id))]
                if images:
                    img = random.choice(images)
                    file = discord.File(os.path.join(RESPONSES_FOLDER, img), filename="yuno.png")
                    await message.reply(file=file, mention_author=False)
                else:
                    await message.reply(random.choice(self.default_responses), mention_author=False)
            return

        # Send the matched response
        if response_data.get('image_path') and os.path.exists(response_data['image_path']):
            file = discord.File(response_data['image_path'], filename="response.png")
            if response_data.get('response'):
                await message.reply(response_data['response'], file=file, mention_author=False)
            else:
                await message.reply(file=file, mention_author=False)
        elif response_data.get('response'):
            await message.reply(response_data['response'], mention_author=False)

    # === SLASH COMMANDS ===
    @app_commands.command(name="add-response", description="Add a custom mention response")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        trigger="The word/phrase that triggers this response",
        response="The text response to send"
    )
    async def slash_add_response(self, interaction: discord.Interaction, trigger: str, response: str):
        """Slash command to add mention response"""
        with get_db() as conn:
            conn.execute("""
                INSERT INTO mention_responses (guild_id, trigger, response, created_by)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(guild_id, trigger) DO UPDATE SET response = ?, created_by = ?
            """, (interaction.guild_id, trigger.lower(), response, interaction.user.id,
                  response, interaction.user.id))

        embed = discord.Embed(
            title="Mention Response Added",
            color=config.COLOR_SUCCESS
        )
        embed.add_field(name="Trigger", value=f"`{trigger}`", inline=True)
        embed.add_field(name="Response", value=response[:1024], inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="del-response", description="Delete a custom mention response")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(trigger="The trigger word to remove")
    async def slash_del_response(self, interaction: discord.Interaction, trigger: str):
        """Slash command to delete mention response"""
        with get_db() as conn:
            result = conn.execute("""
                DELETE FROM mention_responses
                WHERE guild_id = ? AND LOWER(trigger) = LOWER(?)
            """, (interaction.guild_id, trigger))

        if result.rowcount == 0:
            return await interaction.response.send_message(
                f"No response found for trigger `{trigger}`",
                ephemeral=True
            )

        embed = discord.Embed(
            title="Mention Response Deleted",
            description=f"Removed response for trigger `{trigger}`",
            color=config.COLOR_WARNING
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="responses", description="List all custom mention responses")
    async def slash_list_responses(self, interaction: discord.Interaction):
        """Slash command to list mention responses"""
        with get_db() as conn:
            rows = conn.execute("""
                SELECT trigger, response FROM mention_responses
                WHERE guild_id = ? ORDER BY trigger LIMIT 25
            """, (interaction.guild_id,)).fetchall()

        if not rows:
            return await interaction.response.send_message(
                "No custom responses set for this server.",
                ephemeral=True
            )

        embed = discord.Embed(
            title=f"Mention Responses",
            color=config.COLOR_INFO
        )

        for row in rows:
            response_preview = row['response'][:100] if row['response'] else "No text"
            embed.add_field(
                name=f"`{row['trigger']}`",
                value=response_preview,
                inline=False
            )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(MentionResponses(bot))
    logger.info("MentionResponses cog loaded")
