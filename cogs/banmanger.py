import discord
from discord.ext import commands
import json
import asyncio
from datetime import datetime

class BanManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # === EXPORT ALL BANS FROM CURRENT SERVER ===
    @commands.command(name="exportbans")
    @commands.is_owner()
    async def export_bans(self, ctx):
        """Exports the entire ban list as a JSON file"""
        if not ctx.guild:
            return await ctx.send("This command only works in a server.")

        await ctx.send("Fetching ban list... (this may take a while)")

        bans = []
        async for ban_entry in ctx.guild.bans(limit=None):
            bans.append({
                "user_id": ban_entry.user.id,
                "username": str(ban_entry.user),
                "discriminator": ban_entry.user.discriminator,
                "reason": ban_entry.reason or "No reason provided",
                "banned_at": ban_entry.created_at.isoformat() if hasattr(ban_entry, 'created_at') else None
            })

        if not bans:
            return await ctx.send("No bans found in this server.")

        # Create JSON
        data = {
            "guild_id": ctx.guild.id,
            "guild_name": ctx.guild.name,
            "exported_by": str(ctx.author),
            "exported_at": datetime.utcnow().isoformat(),
            "total_bans": len(bans),
            "bans": bans
        }

        filename = f"bans_{ctx.guild.id}_{int(datetime.utcnow().timestamp())}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        file = discord.File(filename)
        await ctx.send(
            f"**Ban list exported!**\n"
            f"Server: `{ctx.guild.name}`\n"
            f"Total bans: `{len(bans)}`\n"
            f"Exported by: {ctx.author.mention}",
            file=file
        )

        # Clean up
        try:
            os.remove(filename)
        except:
            pass

    # === IMPORT BANS INTO CURRENT SERVER ===
    @commands.command(name="importbans")
    @commands.is_owner()
    async def import_bans(self, ctx):
        """Import and apply a ban list from a JSON file"""
        if not ctx.message.attachments:
            return await ctx.send("Please attach a valid ban export JSON file.")

        attachment = ctx.message.attachments[0]
        if not attachment.filename.endswith(".json"):
            return await ctx.send("File must be a JSON export.")

        try:
            data = json.loads(await attachment.read())
        except:
            return await ctx.send("Invalid or corrupted JSON file.")

        if "bans" not in data:
            return await ctx.send("This file doesn't look like a ban export.")

        bans = data.get("bans", [])
        if not bans:
            return await ctx.send("No bans found in the file.")

        # Confirmation
        confirm = await ctx.send(
            f"Ready to import **{len(bans)}** bans into **{ctx.guild.name}**\n"
            f"Type `confirm` within 30 seconds to proceed."
        )

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == "confirm"

        try:
            await self.bot.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            return await confirm.edit(content="Import cancelled.")

        await confirm.edit(content="Importing bans... This may take a while.")

        success = 0
        failed = 0
        already_banned = 0

        for entry in bans:
            user_id = entry.get("user_id")
            reason = entry.get("reason", "Mass ban import")

            if not user_id:
                failed += 1
                continue

            try:
                user = discord.Object(id=user_id)
                await ctx.guild.ban(user, reason=f"[Mass Import] {reason}", delete_message_days=0)
                success += 1
            except discord.NotFound:
                already_banned += 1
            except discord.Forbidden:
                failed += 1
            except Exception:
                failed += 1

            await asyncio.sleep(0.5)  # Rate limit safety

        summary = (
            f"**Ban import complete!**\n\n"
            f"Success: `{success}`\n"
            f"Already banned: `{already_banned}`\n"
            f"Failed: `{failed}`\n"
            f"Total processed: `{len(bans)}`"
        )
        await confirm.edit(content=summary)

    # === QUICK MASS BAN FROM USER IDS (text list) ===
    @commands.command(name="massban")
    @commands.is_owner()
    async def mass_ban(self, ctx, *, user_ids: str):
        """Mass ban by pasting a list of user IDs (one per line)"""
        ids = [uid.strip() for uid in user_ids.replace(",", "\n").split("\n") if uid.strip().isdigit()]
        if not ids:
            return await ctx.send("No valid user IDs found.")

        await ctx.send(f"Mass banning {len(ids)} users... Type `confirm` to proceed.")
        def check(m): return m.author == ctx.author and m.content.lower() == "confirm"
        try:
            await self.bot.wait_for("message", check=check, timeout=30)
        except:
            return await ctx.send("Cancelled.")

        success = 0
        for uid in ids:
            try:
                await ctx.guild.ban(discord.Object(id=int(uid)), reason="Mass ban by owner")
                success += 1
            except:
                pass
            await asyncio.sleep(0.5)

        await ctx.send(f"Mission complete. {success}/{len(ids)} banned.")

async def setup(bot):
    await bot.add_cog(BanManager(bot))
    print("Ban import/export system loaded — total control achieved.")
