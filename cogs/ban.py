import discord
from discord.ext import commands
import random
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

BAN_IMAGES_FOLDER = "ban_images"
os.makedirs(BAN_IMAGES_FOLDER, exist_ok=True)

class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.default_ban_image = "ban_images/default.png"
        self.custom_ban_images = {}

    @commands.command(name="setdefaultban")
    @commands.is_owner()
    async def set_default(self, ctx):
        if not ctx.message.attachments:
            return await ctx.send("Attach an image.")
        attachment = ctx.message.attachments[0]
        if not attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            return await ctx.send("Only images.")
        path = f"{BAN_IMAGES_FOLDER}/default.png"
        await attachment.save(path)
        self.default_ban_image = path
        await ctx.send("Default ban image updated.")

    @commands.command(name="setmyban")
    @commands.has_permissions(ban_members=True)
    async def set_personal(self, ctx):
        if not ctx.message.attachments:
            return await ctx.send("Attach your custom ban image.")
        attachment = ctx.message.attachments[0]
        if not attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            return await ctx.send("Only images.")
        path = f"{BAN_IMAGES_FOLDER}/{ctx.author.id}.png"
        await attachment.save(path)
        self.custom_ban_images[ctx.author.id] = path
        await ctx.send("Your personal ban image is set.")

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx, target: str, *, reason: str = "No reason provided"):
        if not ctx.author.guild_permissions.ban_members:
            try:
                await ctx.author.ban(reason="[Anti-Abuse] Unauthorized ban attempt", delete_message_seconds=86400)
                return await ctx.send(f"{ctx.author.mention} tried to ban without permission.\nThey're gone. ♡")
            except:
                return await ctx.send("Nice try.")

        member = None
        try:
            member = await commands.MemberConverter().convert(ctx, target)
        except:
            pass

        if not member:
            try:
                user_id = int(target.strip("<@!>").replace("@", ""))
                user = await self.bot.fetch_user(user_id)
                await ctx.guild.ban(discord.Object(id=user.id), reason=f"[ID Ban] {reason} — by {ctx.author}")
                return await self.send_ban_image(ctx, user, reason, ctx.author)
            except:
                return await ctx.send("Invalid user/ID.")

        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send("Can't ban someone equal/higher than you.")

        try:
            await member.ban(reason=f"{reason} — by {ctx.author}", delete_message_seconds=604800)
        except:
            return await ctx.send("Failed to ban.")
        await self.send_ban_image(ctx, member, reason, ctx.author)

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx, user: str, *, reason: str = "No reason provided"):
        target_user = None

        if user.isdigit():
            try:
                target_user = await self.bot.fetch_user(int(user))
            except:
                pass

        elif "#" in user:
            try:
                name, discrim = user.split("#")
                bans = await ctx.guild.bans().flatten()
                for ban_entry in bans:
                    if ban_entry.user.name == name and ban_entry.user.discriminator == discrim:
                        target_user = ban_entry.user
                        break
            except:
                pass

        elif user.startswith("<@"):
            user_id = user.strip("<@!>")
            if user_id.isdigit():
                try:
                    target_user = await self.bot.fetch_user(int(user_id))
                except:
                    pass

        if not target_user:
            return await ctx.send("User not found or not banned.")

        try:
            await ctx.guild.unban(target_user, reason=f"{reason} — by {ctx.author}")
        except discord.NotFound:
            return await ctx.send("User is not banned.")
        except:
            return await ctx.send("Failed to unban.")

        embed = discord.Embed(title="User Unbanned", color=0x00ff00)
        embed.description = f"**{target_user}** (`{target_user.id}`) is free again."
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="By", value=ctx.author.mention, inline=False)
        embed.set_thumbnail(url=target_user.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        await ctx.send(embed=embed)

    async def send_ban_image(self, ctx, user, reason, moderator):
        image_path = self.custom_ban_images.get(moderator.id)
        if not image_path or not os.path.exists(image_path):
            image_path = self.default_ban_image
            if not os.path.exists(image_path):
                files = [f for f in os.listdir(BAN_IMAGES_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
                image_path = os.path.join(BAN_IMAGES_FOLDER, random.choice(files)) if files else None

        if image_path and os.path.exists(image_path):
            file = discord.File(image_path, filename="ban.png")
            embed = discord.Embed(color=0xff003d)
            embed.set_image(url="attachment://ban.png")
            embed.set_footer(text=f"Banned by {moderator} • {reason}")
            await ctx.send(file=file, embed=embed)
        else:
            await ctx.send(f"**{user}** has been banned | {reason}")

async def setup(bot):
    await bot.add_cog(Ban(bot))
