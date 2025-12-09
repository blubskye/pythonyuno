import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import math
import logging
from contextlib import contextmanager
from cogs.utils.checks import is_admin
import config

DB_PATH = config.DB_PATH
logger = logging.getLogger(__name__)

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

def calc_level(exp: int) -> int:
    """Calculate level from experience"""
    return int((math.sqrt(1 + 8 * exp / config.LEVEL_DIVISOR) - 1) / 2)

def calc_exp_for_level(level: int) -> int:
    """Calculate required XP for a level"""
    return int(config.LEVEL_DIVISOR * level * (level + 1) / 2)

class BulkXP(commands.Cog):
    """Bulk XP operations for administrators"""

    def __init__(self, bot):
        self.bot = bot

    async def update_user_roles(self, member: discord.Member):
        """Update roles based on current level"""
        with get_db() as conn:
            user_row = conn.execute("""
                SELECT level FROM glevel WHERE guild_id = ? AND user_id = ?
            """, (member.guild.id, member.id)).fetchone()

            if not user_row:
                return

            user_level = user_row['level']

            # Get all rank rewards
            ranks = conn.execute("""
                SELECT role_id, level FROM ranks WHERE guild_id = ? ORDER BY level DESC
            """, (member.guild.id,)).fetchall()

            for rank in ranks:
                role = member.guild.get_role(rank['role_id'])
                if not role:
                    continue

                try:
                    if user_level >= rank['level'] and role not in member.roles:
                        await member.add_roles(role, reason="Level reward (bulk operation)")
                    elif user_level < rank['level'] and role in member.roles:
                        await member.remove_roles(role, reason="Level reward removed (bulk operation)")
                except discord.Forbidden:
                    logger.warning(f"Cannot modify role {role.name} for {member}")

    # === MASS ADD XP ===
    @commands.command(name="mass-addxp", aliases=["massaddxp", "bulkaddxp"])
    @is_admin()
    async def mass_add_xp(self, ctx, role: discord.Role, amount: int):
        """Add XP to all members with a specific role

        Usage: ?mass-addxp @Role 500
        """
        if amount <= 0:
            return await ctx.send("Amount must be positive.")

        if amount > 100000:
            return await ctx.send("Amount too large. Maximum is 100,000 XP per operation.")

        members = [m for m in role.members if not m.bot]
        if not members:
            return await ctx.send(f"No human members found with role {role.mention}")

        msg = await ctx.send(f"Adding {amount} XP to {len(members)} members...")

        updated = 0
        level_ups = 0

        with get_db() as conn:
            for member in members:
                row = conn.execute("""
                    SELECT exp, level FROM glevel WHERE guild_id = ? AND user_id = ?
                """, (ctx.guild.id, member.id)).fetchone()

                if row:
                    old_exp = row['exp']
                    old_level = row['level']
                else:
                    old_exp = 0
                    old_level = 0
                    conn.execute("""
                        INSERT INTO glevel (guild_id, user_id, exp, level) VALUES (?, ?, 0, 0)
                    """, (ctx.guild.id, member.id))

                new_exp = old_exp + amount
                new_level = calc_level(new_exp)

                conn.execute("""
                    UPDATE glevel SET exp = ?, level = ? WHERE guild_id = ? AND user_id = ?
                """, (new_exp, new_level, ctx.guild.id, member.id))

                updated += 1
                if new_level > old_level:
                    level_ups += 1

        # Update roles for leveled up members
        for member in members:
            try:
                await self.update_user_roles(member)
            except Exception as e:
                logger.error(f"Error updating roles for {member}: {e}")

        embed = discord.Embed(
            title="Bulk XP Added",
            color=config.COLOR_SUCCESS
        )
        embed.add_field(name="Role", value=role.mention, inline=True)
        embed.add_field(name="XP Added", value=f"+{amount:,}", inline=True)
        embed.add_field(name="Members Updated", value=str(updated), inline=True)
        embed.add_field(name="Level Ups", value=str(level_ups), inline=True)
        await msg.edit(content=None, embed=embed)

    # === MASS SET XP ===
    @commands.command(name="mass-setxp", aliases=["masssetxp", "bulksetxp"])
    @is_admin()
    async def mass_set_xp(self, ctx, role: discord.Role, amount: int):
        """Set XP for all members with a specific role

        Usage: ?mass-setxp @Role 1000
        """
        if amount < 0:
            return await ctx.send("Amount cannot be negative.")

        members = [m for m in role.members if not m.bot]
        if not members:
            return await ctx.send(f"No human members found with role {role.mention}")

        msg = await ctx.send(f"Setting XP to {amount} for {len(members)} members...")

        new_level = calc_level(amount)
        updated = 0

        with get_db() as conn:
            for member in members:
                conn.execute("""
                    INSERT INTO glevel (guild_id, user_id, exp, level) VALUES (?, ?, ?, ?)
                    ON CONFLICT(guild_id, user_id) DO UPDATE SET exp = ?, level = ?
                """, (ctx.guild.id, member.id, amount, new_level, amount, new_level))
                updated += 1

        # Update roles
        for member in members:
            try:
                await self.update_user_roles(member)
            except Exception as e:
                logger.error(f"Error updating roles for {member}: {e}")

        embed = discord.Embed(
            title="Bulk XP Set",
            color=config.COLOR_SUCCESS
        )
        embed.add_field(name="Role", value=role.mention, inline=True)
        embed.add_field(name="XP Set To", value=f"{amount:,}", inline=True)
        embed.add_field(name="Level", value=str(new_level), inline=True)
        embed.add_field(name="Members Updated", value=str(updated), inline=True)
        await msg.edit(content=None, embed=embed)

    # === MASS LEVEL UP ===
    @commands.command(name="mass-levelup", aliases=["masslevelup", "bulklevelup"])
    @is_admin()
    async def mass_level_up(self, ctx, role: discord.Role, levels: int = 1):
        """Increase level for all members with a specific role

        Usage: ?mass-levelup @Role 5
        """
        if levels <= 0:
            return await ctx.send("Levels must be positive.")

        if levels > 100:
            return await ctx.send("Maximum 100 levels per operation.")

        members = [m for m in role.members if not m.bot]
        if not members:
            return await ctx.send(f"No human members found with role {role.mention}")

        msg = await ctx.send(f"Increasing level by {levels} for {len(members)} members...")

        updated = 0

        with get_db() as conn:
            for member in members:
                row = conn.execute("""
                    SELECT exp, level FROM glevel WHERE guild_id = ? AND user_id = ?
                """, (ctx.guild.id, member.id)).fetchone()

                if row:
                    old_level = row['level']
                else:
                    old_level = 0
                    conn.execute("""
                        INSERT INTO glevel (guild_id, user_id, exp, level) VALUES (?, ?, 0, 0)
                    """, (ctx.guild.id, member.id))

                new_level = old_level + levels
                new_exp = calc_exp_for_level(new_level)

                conn.execute("""
                    UPDATE glevel SET exp = ?, level = ? WHERE guild_id = ? AND user_id = ?
                """, (new_exp, new_level, ctx.guild.id, member.id))
                updated += 1

        # Update roles
        for member in members:
            try:
                await self.update_user_roles(member)
            except Exception as e:
                logger.error(f"Error updating roles for {member}: {e}")

        embed = discord.Embed(
            title="Bulk Level Up",
            color=config.COLOR_SUCCESS
        )
        embed.add_field(name="Role", value=role.mention, inline=True)
        embed.add_field(name="Levels Added", value=f"+{levels}", inline=True)
        embed.add_field(name="Members Updated", value=str(updated), inline=True)
        await msg.edit(content=None, embed=embed)

    # === SYNC XP FROM ROLES ===
    @commands.command(name="sync-xp-from-roles", aliases=["syncxpfromroles", "rolesync"])
    @is_admin()
    async def sync_xp_from_roles(self, ctx):
        """Sync member XP based on their highest level role

        This sets each member's XP to match their highest level-linked role.
        Useful when importing members with existing roles.
        """
        msg = await ctx.send("Syncing XP from roles...")

        with get_db() as conn:
            # Get all rank rewards
            ranks = conn.execute("""
                SELECT role_id, level FROM ranks WHERE guild_id = ? ORDER BY level DESC
            """, (ctx.guild.id,)).fetchall()

            if not ranks:
                return await msg.edit(content="No level roles configured. Use `?ranks add` first.")

            updated = 0
            for member in ctx.guild.members:
                if member.bot:
                    continue

                # Find highest role the member has
                highest_level = 0
                for rank in ranks:
                    role = ctx.guild.get_role(rank['role_id'])
                    if role and role in member.roles:
                        highest_level = max(highest_level, rank['level'])

                if highest_level > 0:
                    exp = calc_exp_for_level(highest_level)
                    conn.execute("""
                        INSERT INTO glevel (guild_id, user_id, exp, level) VALUES (?, ?, ?, ?)
                        ON CONFLICT(guild_id, user_id) DO UPDATE SET exp = ?, level = ?
                    """, (ctx.guild.id, member.id, exp, highest_level, exp, highest_level))
                    updated += 1

        embed = discord.Embed(
            title="XP Synced from Roles",
            description=f"Updated {updated} members based on their level roles.",
            color=config.COLOR_SUCCESS
        )
        await msg.edit(content=None, embed=embed)

    # === SYNC LEVEL ROLES ===
    @commands.command(name="sync-levelroles", aliases=["synclevelroles", "applyroles"])
    @is_admin()
    async def sync_level_roles(self, ctx):
        """Apply level roles to all members based on their current XP

        This ensures all members have the correct roles for their level.
        """
        msg = await ctx.send("Syncing level roles...")

        with get_db() as conn:
            ranks = conn.execute("""
                SELECT role_id, level FROM ranks WHERE guild_id = ? ORDER BY level
            """, (ctx.guild.id,)).fetchall()

            if not ranks:
                return await msg.edit(content="No level roles configured.")

            users = conn.execute("""
                SELECT user_id, level FROM glevel WHERE guild_id = ?
            """, (ctx.guild.id,)).fetchall()

        updated = 0
        errors = 0

        for user in users:
            member = ctx.guild.get_member(user['user_id'])
            if not member or member.bot:
                continue

            try:
                await self.update_user_roles(member)
                updated += 1
            except Exception as e:
                logger.error(f"Error syncing roles for {member}: {e}")
                errors += 1

        embed = discord.Embed(
            title="Level Roles Synced",
            color=config.COLOR_SUCCESS
        )
        embed.add_field(name="Members Updated", value=str(updated), inline=True)
        if errors:
            embed.add_field(name="Errors", value=str(errors), inline=True)
        await msg.edit(content=None, embed=embed)

    # === XP LEADERBOARD ===
    @commands.command(name="xp", aliases=["level", "rank"])
    async def show_xp(self, ctx, member: discord.Member = None):
        """Show your XP and level, or another member's"""
        member = member or ctx.author

        with get_db() as conn:
            row = conn.execute("""
                SELECT exp, level FROM glevel WHERE guild_id = ? AND user_id = ?
            """, (ctx.guild.id, member.id)).fetchone()

            if not row:
                return await ctx.send(f"{member.display_name} has no XP yet.")

            # Get rank
            rank_row = conn.execute("""
                SELECT COUNT(*) + 1 as rank FROM glevel
                WHERE guild_id = ? AND exp > ?
            """, (ctx.guild.id, row['exp'])).fetchone()

        exp = row['exp']
        level = row['level']
        rank = rank_row['rank'] if rank_row else 1

        # Calculate progress to next level
        current_level_exp = calc_exp_for_level(level)
        next_level_exp = calc_exp_for_level(level + 1)
        progress = exp - current_level_exp
        needed = next_level_exp - current_level_exp
        progress_pct = (progress / needed * 100) if needed > 0 else 100

        # Create progress bar
        bar_length = 20
        filled = int(bar_length * progress / needed) if needed > 0 else bar_length
        bar = "" * filled + "" * (bar_length - filled)

        embed = discord.Embed(
            title=f"{member.display_name}'s Level",
            color=config.COLOR_PRIMARY
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Level", value=str(level), inline=True)
        embed.add_field(name="XP", value=f"{exp:,}", inline=True)
        embed.add_field(name="Rank", value=f"#{rank}", inline=True)
        embed.add_field(
            name=f"Progress to Level {level + 1}",
            value=f"`{bar}` {progress_pct:.1f}%\n{progress:,} / {needed:,} XP",
            inline=False
        )
        await ctx.send(embed=embed)

    @commands.command(name="leaderboard", aliases=["lb", "top"])
    async def leaderboard(self, ctx, page: int = 1):
        """Show the XP leaderboard"""
        per_page = 10
        offset = (page - 1) * per_page

        with get_db() as conn:
            rows = conn.execute("""
                SELECT user_id, exp, level FROM glevel
                WHERE guild_id = ?
                ORDER BY exp DESC
                LIMIT ? OFFSET ?
            """, (ctx.guild.id, per_page, offset)).fetchall()

            total = conn.execute("""
                SELECT COUNT(*) as count FROM glevel WHERE guild_id = ?
            """, (ctx.guild.id,)).fetchone()['count']

        if not rows:
            return await ctx.send("No leaderboard data yet.")

        embed = discord.Embed(
            title=f"Leaderboard - {ctx.guild.name}",
            color=config.COLOR_PRIMARY
        )

        description_lines = []
        for i, row in enumerate(rows, start=offset + 1):
            member = ctx.guild.get_member(row['user_id'])
            name = member.display_name if member else f"Unknown ({row['user_id']})"

            medal = ""
            if i == 1:
                medal = ""
            elif i == 2:
                medal = ""
            elif i == 3:
                medal = ""

            description_lines.append(
                f"{medal}**#{i}** {name}\n"
                f"   Level {row['level']} | {row['exp']:,} XP"
            )

        embed.description = "\n".join(description_lines)

        total_pages = (total + per_page - 1) // per_page
        embed.set_footer(text=f"Page {page}/{total_pages} | {total} members ranked")

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(BulkXP(bot))
    logger.info("BulkXP cog loaded")
