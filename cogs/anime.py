import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import logging
import html
import config

logger = logging.getLogger(__name__)

JIKAN_BASE = "https://api.jikan.moe/v4"

class Anime(commands.Cog):
    """Anime and manga search commands using Jikan API (MyAnimeList)"""

    def __init__(self, bot):
        self.bot = bot
        self.session = None

    async def cog_load(self):
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        if self.session:
            await self.session.close()

    async def search_jikan(self, endpoint: str, query: str, limit: int = 1):
        """Search Jikan API"""
        try:
            url = f"{JIKAN_BASE}/{endpoint}"
            params = {"q": query, "limit": limit, "sfw": "true"}

            async with self.session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("data", [])
                elif resp.status == 429:
                    logger.warning("Jikan API rate limited")
                    return None
                else:
                    logger.error(f"Jikan API error: {resp.status}")
                    return []
        except Exception as e:
            logger.error(f"Error searching Jikan: {e}")
            return []

    def truncate(self, text: str, length: int = 1024) -> str:
        """Truncate text to fit Discord embed limits"""
        if not text:
            return "No description available."
        text = html.unescape(text)
        if len(text) <= length:
            return text
        return text[:length - 3] + "..."

    # === ANIME SEARCH ===
    @commands.command(name="anime")
    async def anime_search(self, ctx, *, query: str):
        """Search for an anime on MyAnimeList

        Usage: ?anime Mirai Nikki
        """
        async with ctx.typing():
            results = await self.search_jikan("anime", query)

        if results is None:
            return await ctx.send("API rate limited. Please try again in a moment.")

        if not results:
            return await ctx.send(f"No anime found for `{query}`")

        anime = results[0]

        embed = discord.Embed(
            title=anime.get("title", "Unknown"),
            url=anime.get("url"),
            color=config.COLOR_PRIMARY
        )

        if anime.get("title_english") and anime["title_english"] != anime["title"]:
            embed.add_field(name="English Title", value=anime["title_english"], inline=False)

        if anime.get("images", {}).get("jpg", {}).get("large_image_url"):
            embed.set_thumbnail(url=anime["images"]["jpg"]["large_image_url"])

        # Synopsis
        synopsis = anime.get("synopsis")
        if synopsis:
            embed.add_field(name="Synopsis", value=self.truncate(synopsis, 500), inline=False)

        # Info fields
        if anime.get("type"):
            embed.add_field(name="Type", value=anime["type"], inline=True)
        if anime.get("episodes"):
            embed.add_field(name="Episodes", value=str(anime["episodes"]), inline=True)
        if anime.get("status"):
            embed.add_field(name="Status", value=anime["status"], inline=True)
        if anime.get("score"):
            embed.add_field(name="Score", value=f"{anime['score']}", inline=True)
        if anime.get("rank"):
            embed.add_field(name="Rank", value=f"#{anime['rank']}", inline=True)
        if anime.get("popularity"):
            embed.add_field(name="Popularity", value=f"#{anime['popularity']}", inline=True)

        # Aired dates
        aired = anime.get("aired", {})
        if aired.get("string"):
            embed.add_field(name="Aired", value=aired["string"], inline=True)

        # Genres
        genres = anime.get("genres", [])
        if genres:
            genre_names = ", ".join(g["name"] for g in genres[:5])
            embed.add_field(name="Genres", value=genre_names, inline=True)

        # Studios
        studios = anime.get("studios", [])
        if studios:
            studio_names = ", ".join(s["name"] for s in studios[:3])
            embed.add_field(name="Studio", value=studio_names, inline=True)

        embed.set_footer(text="Data from MyAnimeList via Jikan API")
        await ctx.send(embed=embed)

    # === MANGA SEARCH ===
    @commands.command(name="manga")
    async def manga_search(self, ctx, *, query: str):
        """Search for a manga on MyAnimeList

        Usage: ?manga Mirai Nikki
        """
        async with ctx.typing():
            results = await self.search_jikan("manga", query)

        if results is None:
            return await ctx.send("API rate limited. Please try again in a moment.")

        if not results:
            return await ctx.send(f"No manga found for `{query}`")

        manga = results[0]

        embed = discord.Embed(
            title=manga.get("title", "Unknown"),
            url=manga.get("url"),
            color=config.COLOR_PRIMARY
        )

        if manga.get("title_english") and manga["title_english"] != manga["title"]:
            embed.add_field(name="English Title", value=manga["title_english"], inline=False)

        if manga.get("images", {}).get("jpg", {}).get("large_image_url"):
            embed.set_thumbnail(url=manga["images"]["jpg"]["large_image_url"])

        # Synopsis
        synopsis = manga.get("synopsis")
        if synopsis:
            embed.add_field(name="Synopsis", value=self.truncate(synopsis, 500), inline=False)

        # Info fields
        if manga.get("type"):
            embed.add_field(name="Type", value=manga["type"], inline=True)
        if manga.get("chapters"):
            embed.add_field(name="Chapters", value=str(manga["chapters"]), inline=True)
        if manga.get("volumes"):
            embed.add_field(name="Volumes", value=str(manga["volumes"]), inline=True)
        if manga.get("status"):
            embed.add_field(name="Status", value=manga["status"], inline=True)
        if manga.get("score"):
            embed.add_field(name="Score", value=f"{manga['score']}", inline=True)
        if manga.get("rank"):
            embed.add_field(name="Rank", value=f"#{manga['rank']}", inline=True)

        # Published dates
        published = manga.get("published", {})
        if published.get("string"):
            embed.add_field(name="Published", value=published["string"], inline=True)

        # Genres
        genres = manga.get("genres", [])
        if genres:
            genre_names = ", ".join(g["name"] for g in genres[:5])
            embed.add_field(name="Genres", value=genre_names, inline=True)

        # Authors
        authors = manga.get("authors", [])
        if authors:
            author_names = ", ".join(a["name"] for a in authors[:3])
            embed.add_field(name="Author", value=author_names, inline=True)

        embed.set_footer(text="Data from MyAnimeList via Jikan API")
        await ctx.send(embed=embed)

    # === CHARACTER SEARCH ===
    @commands.command(name="character", aliases=["char"])
    async def character_search(self, ctx, *, query: str):
        """Search for an anime/manga character

        Usage: ?character Yuno Gasai
        """
        async with ctx.typing():
            results = await self.search_jikan("characters", query)

        if results is None:
            return await ctx.send("API rate limited. Please try again in a moment.")

        if not results:
            return await ctx.send(f"No character found for `{query}`")

        char = results[0]

        embed = discord.Embed(
            title=char.get("name", "Unknown"),
            url=char.get("url"),
            color=config.COLOR_PRIMARY
        )

        if char.get("name_kanji"):
            embed.description = char["name_kanji"]

        if char.get("images", {}).get("jpg", {}).get("image_url"):
            embed.set_thumbnail(url=char["images"]["jpg"]["image_url"])

        # About
        about = char.get("about")
        if about:
            embed.add_field(name="About", value=self.truncate(about, 1000), inline=False)

        if char.get("favorites"):
            embed.add_field(name="Favorites", value=f"{char['favorites']:,}", inline=True)

        embed.set_footer(text="Data from MyAnimeList via Jikan API")
        await ctx.send(embed=embed)

    # === RANDOM ANIME ===
    @commands.command(name="randomnime", aliases=["randomanime"])
    async def random_anime(self, ctx):
        """Get a random anime recommendation"""
        async with ctx.typing():
            try:
                async with self.session.get(f"{JIKAN_BASE}/random/anime") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        anime = data.get("data")
                    else:
                        return await ctx.send("Could not fetch random anime.")
            except Exception as e:
                logger.error(f"Error fetching random anime: {e}")
                return await ctx.send("Error fetching random anime.")

        if not anime:
            return await ctx.send("Could not fetch random anime.")

        embed = discord.Embed(
            title=anime.get("title", "Unknown"),
            url=anime.get("url"),
            color=config.COLOR_PRIMARY
        )

        if anime.get("images", {}).get("jpg", {}).get("large_image_url"):
            embed.set_image(url=anime["images"]["jpg"]["large_image_url"])

        synopsis = anime.get("synopsis")
        if synopsis:
            embed.add_field(name="Synopsis", value=self.truncate(synopsis, 300), inline=False)

        if anime.get("score"):
            embed.add_field(name="Score", value=f"{anime['score']}", inline=True)
        if anime.get("episodes"):
            embed.add_field(name="Episodes", value=str(anime["episodes"]), inline=True)
        if anime.get("type"):
            embed.add_field(name="Type", value=anime["type"], inline=True)

        embed.set_footer(text="Random anime recommendation")
        await ctx.send(embed=embed)

    # === SLASH COMMANDS ===
    @app_commands.command(name="anime", description="Search for an anime")
    @app_commands.describe(query="The anime to search for")
    async def slash_anime(self, interaction: discord.Interaction, query: str):
        """Slash command for anime search"""
        await interaction.response.defer()

        results = await self.search_jikan("anime", query)

        if results is None:
            return await interaction.followup.send("API rate limited. Please try again.")

        if not results:
            return await interaction.followup.send(f"No anime found for `{query}`")

        anime = results[0]

        embed = discord.Embed(
            title=anime.get("title", "Unknown"),
            url=anime.get("url"),
            color=config.COLOR_PRIMARY
        )

        if anime.get("images", {}).get("jpg", {}).get("large_image_url"):
            embed.set_thumbnail(url=anime["images"]["jpg"]["large_image_url"])

        synopsis = anime.get("synopsis")
        if synopsis:
            embed.add_field(name="Synopsis", value=self.truncate(synopsis, 500), inline=False)

        if anime.get("score"):
            embed.add_field(name="Score", value=f"{anime['score']}", inline=True)
        if anime.get("episodes"):
            embed.add_field(name="Episodes", value=str(anime["episodes"]), inline=True)
        if anime.get("status"):
            embed.add_field(name="Status", value=anime["status"], inline=True)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="manga", description="Search for a manga")
    @app_commands.describe(query="The manga to search for")
    async def slash_manga(self, interaction: discord.Interaction, query: str):
        """Slash command for manga search"""
        await interaction.response.defer()

        results = await self.search_jikan("manga", query)

        if results is None:
            return await interaction.followup.send("API rate limited. Please try again.")

        if not results:
            return await interaction.followup.send(f"No manga found for `{query}`")

        manga = results[0]

        embed = discord.Embed(
            title=manga.get("title", "Unknown"),
            url=manga.get("url"),
            color=config.COLOR_PRIMARY
        )

        if manga.get("images", {}).get("jpg", {}).get("large_image_url"):
            embed.set_thumbnail(url=manga["images"]["jpg"]["large_image_url"])

        synopsis = manga.get("synopsis")
        if synopsis:
            embed.add_field(name="Synopsis", value=self.truncate(synopsis, 500), inline=False)

        if manga.get("score"):
            embed.add_field(name="Score", value=f"{manga['score']}", inline=True)
        if manga.get("chapters"):
            embed.add_field(name="Chapters", value=str(manga["chapters"]), inline=True)
        if manga.get("status"):
            embed.add_field(name="Status", value=manga["status"], inline=True)

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Anime(bot))
    logger.info("Anime cog loaded")
