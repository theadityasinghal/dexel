import discord
from discord import app_commands
from discord.ext import commands
from utils.helpers_new import *
import asyncio
from utils.hyperparams import *
from typing import Optional

class Info(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="profile", description="View your profile or someone else's.")
    @app_commands.describe(user="The user to view (defaults to yourself)")
    async def profile(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        member: discord.Member = user or interaction.user
        guild = interaction.guild
        member = guild.get_member(member.id) or member  # pull the cached copy with real presence data
        
        # Member object from cache doesn't carry banner/accent_color — need a fetch for that.
        try:
            full_user = await self.bot.fetch_user(member.id)
        except discord.HTTPException:
            full_user = member  # fallback; banner/accent_color just won't be available

        avatar_url = member.display_avatar.url
        banner_url = full_user.banner.url if full_user.banner else None

        # ---- Status ----
        status_map = {
            discord.Status.online: "🟢 Online",
            discord.Status.idle: "🌙 Idle",
            discord.Status.dnd: "⛔ Do Not Disturb",
            discord.Status.offline: "⚫ Offline / Invisible",
        }
        status_text = status_map.get(member.status, "Unknown")

        # ---- Badges ----
        flag_labels = {
            "staff": "🛠️ Discord Staff",
            "partner": "🤝 Partner",
            "hypesquad": "🎉 HypeSquad Events",
            "hypesquad_bravery": "🦁 Bravery",
            "hypesquad_brilliance": "🧠 Brilliance",
            "hypesquad_balance": "⚖️ Balance",
            "bug_hunter": "🐛 Bug Hunter",
            "bug_hunter_level_2": "🐛 Bug Hunter (Gold)",
            "early_supporter": "🌟 Early Supporter",
            "verified_bot_developer": "✅ Verified Bot Developer",
            "active_developer": "💻 Active Developer",
            "discord_certified_moderator": "🛡️ Certified Moderator",
        }
        badges = [flag_labels[flag] for flag, value in member.public_flags if value and flag in flag_labels]
        badges_text = ", ".join(badges) if badges else "None"

        # ---- Accent color ----
        accent_text = str(full_user.accent_color) if full_user.accent_color else "Not set"

        # ---- Account type ----
        if member.bot:
            account_type = "🤖 Bot Account"
        elif member.system:
            account_type = "⚙️ System Account"
        else:
            account_type = "👤 User Account"

        # ---- Current activity ----
        activity_text = "None"
        if member.activities:
            act = member.activities[0]
            if isinstance(act, discord.Spotify):
                activity_text = f"🎵 Listening to **{act.title}** by {act.artist}"
            elif isinstance(act, discord.Streaming):
                activity_text = f"📡 Streaming **{act.name}**"
            elif isinstance(act, discord.CustomActivity):
                activity_text = f"💬 {act.name}" if act.name else "Custom status"
            elif isinstance(act, discord.Game):
                activity_text = f"🎮 Playing **{act.name}**"
            elif isinstance(act, discord.Activity):
                activity_text = f"🕹️ {act.name}"

        # ---- Join position ----
        joined_members = sorted((m for m in guild.members if m.joined_at), key=lambda m: m.joined_at)
        try:
            join_position = joined_members.index(member) + 1
        except ValueError:
            join_position = "Unknown"

        # ---- Boosting ----
        if member.premium_since:
            boosting_text = f"Yes — since <t:{int(member.premium_since.timestamp())}:D>"
        else:
            boosting_text = "Not boosting"

        # ---- Roles ----
        roles = sorted((r for r in member.roles if r != guild.default_role), key=lambda r: r.position, reverse=True)
        roles_text = ", ".join(r.mention for r in roles) if roles else "None"
        if len(roles_text) > 1024:
            roles_text = roles_text[:1000] + "… (truncated)"

        # ---- Permissions ----
        perms = member.guild_permissions
        if perms.administrator:
            perms_text = "Administrator (implies all permissions)"
        else:
            granted = [name.replace("_", " ").title() for name, value in perms if value]
            perms_text = ", ".join(granted) if granted else "None"
            if len(perms_text) > 1024:
                perms_text = perms_text[:1000] + "… (truncated)"

        # ---- Embed accent color from top role ----
        top_role_color = member.top_role.color
        embed_color = top_role_color if top_role_color.value != 0 else discord.Color.blurple()

        embed = discord.Embed(
            description=f"[{member.global_name or member.name}]({avatar_url})",
            color=embed_color,
        )
        embed.set_thumbnail(url=avatar_url)
        if banner_url:
            embed.set_image(url=banner_url)

        # User-specific
        embed.add_field(name="Nickname", value=member.nick or "None", inline=True)
        embed.add_field(name="User ID", value=str(member.id), inline=True)
        embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:D>", inline=True)
        embed.add_field(name="Status", value=status_text, inline=True)
        embed.add_field(name="Account Type", value=account_type, inline=True)
        embed.add_field(name="Accent Color", value=accent_text, inline=True)
        embed.add_field(name="Badges", value=badges_text, inline=False)
        embed.add_field(name="Current Activity", value=activity_text, inline=False)

        # Guild-specific
        embed.add_field(name="Join Position", value=f"#{join_position}", inline=True)
        embed.add_field(name="Boosting", value=boosting_text, inline=True)
        embed.add_field(name="Roles", value=roles_text, inline=False)
        embed.add_field(name="Permissions", value=perms_text, inline=False)

        embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Info(bot))
