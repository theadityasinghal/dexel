import re
import asyncio
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from urllib.parse import urlencode
import xml.etree.ElementTree as ET

from utils.helpers.helpers_new import LLMHelper  # adjust import path


class PaperView(discord.ui.View):
    def __init__(self, title: str, abstract: str, arxiv_id: str, llm_instance):
        super().__init__(timeout=None)
        self.title = title
        self.abstract = abstract
        self.llm_instance = llm_instance
        self.clicked = False

        self.add_item(discord.ui.Button(
            label="PDF",
            emoji="📄",
            style=discord.ButtonStyle.link,
            url=f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        ))

    @discord.ui.button(label="Explain Like I'm 5", emoji="🧒", style=discord.ButtonStyle.primary)
    async def eli5_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.clicked:
            await interaction.response.send_message("Already being explained!", ephemeral=True)
            return

        self.clicked = True
        button.disabled = True
        await interaction.response.edit_message(view=self)

        prompt = (
            f"Explain this paper like I'm 5. You can use a maximum of 5 sentences, 1500 tokens. No jargon.\n"
            f"Title: {self.title}\n"
            f"Abstract: {self.abstract}"
        )

        response = await self.llm_instance.askllm(prompt)

        embed = discord.Embed(
            title="🧒 ELI5",
            description=response,
            color=discord.Color.green()
        )

        await interaction.channel.send(embed=embed, reference=interaction.message)


class Paper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.LLMinstance = LLMHelper()

    def _extract_arxiv_id(self, query: str) -> str:
        match = re.search(r'(\d{4}\.\d{5})', query)
        if match:
            return match.group(1)
        return query  # treat as title search

    async def _fetch_paper(self, session: aiohttp.ClientSession, query: str) -> dict | None:
        base_url = "http://export.arxiv.org/api/query?"

        if re.match(r'\d{4}\.\d{5}', query):
            search_query = f"id:{query}"
        else:
            search_query = f'ti:"{query}"'

        params = {"search_query": search_query, "max_results": 1, "sortBy": "relevance"}

        async with session.get(base_url + urlencode(params)) as resp:
            if resp.status != 200:
                return None
            return self._parse_arxiv_xml(await resp.text())

    def _parse_arxiv_xml(self, xml: str) -> dict | None:
        root = ET.fromstring(xml)
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'arxiv': 'http://arxiv.org/schemas/atom'
        }
        entry = root.find('atom:entry', ns)
        if entry is None:
            return None

        primary_cat = entry.find('arxiv:primary_category', ns)
        category = primary_cat.get('term') if primary_cat is not None else "Unknown"

        return {
            'id': entry.find('atom:id', ns).text.split('/abs/')[-1],
            'title': entry.find('atom:title', ns).text.strip().replace('\n', ' '),
            'authors': [a.find('atom:name', ns).text for a in entry.findall('atom:author', ns)],
            'published': entry.find('atom:published', ns).text[:10],
            'summary': entry.find('atom:summary', ns).text.strip().replace('\n', ' '),
            'category': category,
        }

    async def _fetch_citations(self, session: aiohttp.ClientSession, arxiv_id: str) -> int | None:
        url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{arxiv_id}?fields=citationCount"
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            return data.get('citationCount')

    def _build_embed(self, data: dict, citations: int | None) -> discord.Embed:
        embed = discord.Embed(
            title=data['title'][:256],
            url=f"https://arxiv.org/abs/{data['id']}",
            color=discord.Color.blue()
        )

        authors = ", ".join(data['authors'][:3])
        if len(data['authors']) > 3:
            authors += f" +{len(data['authors']) - 3} more"

        embed.add_field(name="Authors", value=authors, inline=False)
        embed.add_field(name="Published", value=data['published'], inline=True)
        embed.add_field(name="Category", value=data['category'], inline=True)

        summary = data['summary']
        if len(summary) > 500:
            summary = summary[:497] + "..."
        embed.add_field(name="Abstract", value=summary, inline=False)

        footer = f"arXiv:{data['id']}"
        if citations is not None:
            footer += f" • 📚 {citations:,} citations"
        embed.set_footer(text=footer)

        return embed

    @app_commands.command(name="paper", description="Look up an ML research paper")
    @app_commands.describe(query="arXiv ID, URL, or paper title (typos OK)")
    async def paper(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()

        try:
            arxiv_id = self._extract_arxiv_id(query)

            async with aiohttp.ClientSession() as session:
                paper_data = await self._fetch_paper(session, arxiv_id)

                if not paper_data:
                    await interaction.followup.send("❌ Paper not found. Try an arXiv ID or clearer title.")
                    return

                citations = await self._fetch_citations(session, paper_data['id'])

            embed = self._build_embed(paper_data, citations)
            view = PaperView(paper_data['title'], paper_data['summary'], paper_data['id'], self.LLMinstance)

            await interaction.followup.send(embed=embed, view=view)

        except Exception as e:
            await interaction.followup.send(f"❌ Something went wrong: {str(e)[:100]}")


async def setup(bot):
    await bot.add_cog(Paper(bot))