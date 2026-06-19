import discord
from discord import app_commands
import enum
import asyncio
from utils.helpers.helpers_new import *
from utils.helpers.neon import Database
from utils.hyperparams import *
import traceback
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter
import io


class GreetingType(enum.Enum):
    join = "join"
    leave = "leave"


class Greeting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.BASE_DIR = Path(__file__).resolve().parent.parent  # utils/ -> project root
        self.ASSETS_DIR = self.BASE_DIR / "assets"
        self.WELCOME_BACKGROUND_PATH = self.ASSETS_DIR / "welcome_bg1.png"
        self.FONT_PATH = self.ASSETS_DIR / "Inter" / "static" / "Inter_24pt-Bold.ttf"
        self.AVATAR_SIZE = 200

    def _render(
        self,
        type: GreetingType,
        avatar_bytes: bytes,
        display_name: str,
        member_count: int,
    ) -> io.BytesIO:
        """Sync, CPU-bound. Called via asyncio.to_thread so it doesn't block the event loop."""
        SS = 4  # supersample factor for anti-aliasing the mask/ring
        size = self.AVATAR_SIZE
        ring_width = 8

        avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((size, size))

        # anti-aliased circular mask: draw big, downsample
        mask_big = Image.new("L", (size * SS, size * SS), 0)
        ImageDraw.Draw(mask_big).ellipse((0, 0, size * SS, size * SS), fill=255)
        mask = mask_big.resize((size, size), Image.LANCZOS)
        avatar.putalpha(mask)

        # solid white ring, drawn as its own anti-aliased layer sized slightly bigger than the avatar
        ring_size = size + ring_width * 2
        ring_big = Image.new("RGBA", (ring_size * SS, ring_size * SS), (0, 0, 0, 0))
        ImageDraw.Draw(ring_big).ellipse(
            (0, 0, ring_size * SS, ring_size * SS), fill=(255, 255, 255, 255)
        )
        ring = ring_big.resize((ring_size, ring_size), Image.LANCZOS)
        # punch the avatar-sized hole out of the ring so it reads as a stroke, not a filled disc
        hole_big = Image.new("L", (ring_size * SS, ring_size * SS), 0)
        inset = ring_width * SS
        ImageDraw.Draw(hole_big).ellipse(
            (inset, inset, ring_size * SS - inset, ring_size * SS - inset), fill=255
        )
        hole = hole_big.resize((ring_size, ring_size), Image.LANCZOS)
        ring.putalpha(ImageChops.subtract(ring.getchannel("A"), hole))

        # soft drop shadow behind the ring
        shadow = Image.new("RGBA", (ring_size, ring_size), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).ellipse((0, 0, ring_size, ring_size), fill=(0, 0, 0, 120))
        shadow = shadow.filter(ImageFilter.GaussianBlur(8))

        bg = Image.open(str(self.WELCOME_BACKGROUND_PATH)).convert("RGBA").resize((900, 400))

        avatar_top = 80
        ring_pos = ((bg.width - ring_size) // 2, avatar_top - ring_width)
        shadow_pos = (ring_pos[0], ring_pos[1] + 6)  # offset down slightly for depth
        avatar_pos = ((bg.width - size) // 2, avatar_top)

        bg.alpha_composite(shadow, shadow_pos)
        bg.alpha_composite(ring, ring_pos)
        bg.alpha_composite(avatar, avatar_pos)

        draw = ImageDraw.Draw(bg)

        # auto-shrink the name font so long usernames never overflow the card width
        name_text = display_name
        max_width = bg.width - 80
        font_size = 40
        font = ImageFont.truetype(str(self.FONT_PATH), font_size)
        while draw.textlength(name_text, font=font) > max_width and font_size > 18:
            font_size -= 2
            font = ImageFont.truetype(str(self.FONT_PATH), font_size)
        name_w = draw.textlength(name_text, font=font)
        name_y = avatar_pos[1] + size + 30
        draw.text(((bg.width - name_w) / 2, name_y), name_text, font=font, fill="white")

        # member count subtitle
        sub_font = ImageFont.truetype(str(self.FONT_PATH), 20)
        sub_text = f"Member #{member_count}"
        sub_w = draw.textlength(sub_text, font=sub_font)
        sub_y = name_y + font_size + 8
        draw.text(((bg.width - sub_w) / 2, sub_y), sub_text, font=sub_font, fill=(220, 220, 220, 255))

        buf = io.BytesIO()
        bg.save(buf, format="PNG")
        buf.seek(0)
        return buf

    async def generate_image(self, type: GreetingType, member: discord.Member) -> io.BytesIO:
        avatar_bytes = await member.display_avatar.read()
        return await asyncio.to_thread(
            self._render, type, avatar_bytes, member.display_name, member.guild.member_count
        )

    @app_commands.command(name="greeting")
    @app_commands.describe(
        type="Configure join or leave greetings (leave blank to just view current config)",
        channel="Channel where this greeting will be posted",
        message="Custom message — use {mention}, {username}, {server} as placeholders"
    )
    async def greeting(
        self,
        interaction: discord.Interaction,
        type: GreetingType | None = None,            # optional, shows as dropdown
        channel: discord.TextChannel | None = None,  # optional, shows channel picker
        message: str | None = None                   # optional, free text
    ):
        await interaction.response.defer()

        if type is None and (channel is not None or message is not None):
            embed = discord.Embed(title="Invalid Arguments",
                                   description="Select `type: join | leave`")
            await interaction.followup.send(embed=embed)
            return

        if type == GreetingType.join:
            if channel is not None:
                self.bot.db.set_join_channel(guild_id=interaction.guild.id, channel_id=channel.id)
            if message is not None:
                self.bot.db.set_join_message(guild_id=interaction.guild.id, message=message)
        elif type == GreetingType.leave:
            if channel is not None:
                self.bot.db.set_leave_channel(guild_id=interaction.guild.id, channel_id=channel.id)
            if message is not None:
                self.bot.db.set_leave_message(guild_id=interaction.guild.id, message=message)

        config = self.bot.db.get_greetings_config(interaction.guild.id)
        join_channel = f"<#{config['join_channel_id']}>" if config['join_channel_id'] else "Not set"
        join_message = config['join_message'] or DEFAULT_JOIN_MESSAGE
        leave_channel = f"<#{config['leave_channel_id']}>" if config['leave_channel_id'] else "Not set"
        leave_message = config['leave_message'] or DEFAULT_LEAVE_MESSAGE

        description = (
            f"**Join channel:** {join_channel}\n"
            f"**Join message:** _{join_message}_\n"
            f"**Leave channel:** {leave_channel}\n"
            f"**Leave message:** _{leave_message}_"
        )

        embed = discord.Embed(title="Greetings Config",
                               description=description)

        await interaction.followup.send(embed=embed)
        return

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        config = self.bot.db.get_greetings_config(member.guild.id)
        if config['join_channel_id'] is None:
            return
        channel = member.guild.get_channel(config['join_channel_id'])
        if channel is None:
            try:
                channel = await member.guild.fetch_channel(config['join_channel_id'])
            except discord.HTTPException:
                return
        join_message = config['join_message'] or DEFAULT_JOIN_MESSAGE
        message = join_message.format(
            mention=member.mention,
            username=member.display_name,
            server=member.guild.name,
        )

        try:
            buf = await asyncio.wait_for(
                self.generate_image(type=GreetingType.join, member=member), timeout=5
            )
            file = discord.File(buf, filename="welcome.png")
            embed = discord.Embed(
                title=f"{member.display_name} × {member.guild.name}",
                description=message,
                color=discord.Color.green(),
            )
            embed.set_footer(text=f"Member #{member.guild.member_count}")
            embed.set_image(url="attachment://welcome.png")
            embed.set_footer(text=f"{member.guild.name} • Member #{member.guild.member_count}")
            await channel.send(embed=embed, file=file)
        except asyncio.TimeoutError:
            await channel.send(content=message)
        except Exception:
            # image generation/send failed - don't let a bad welcome image break the join flow
            traceback.print_exc()
            await channel.send(content=message)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        config = self.bot.db.get_greetings_config(member.guild.id)
        if config['leave_channel_id'] is None:
            return
        channel = member.guild.get_channel(config['leave_channel_id'])
        if channel is None:
            try:
                channel = await member.guild.fetch_channel(config['leave_channel_id'])
            except discord.HTTPException:
                return
        leave_message = config['leave_message'] or DEFAULT_LEAVE_MESSAGE
        message = leave_message.format(
            mention=member.mention,
            username=member.display_name,
            server=member.guild.name,
        )

        try:
            buf = await asyncio.wait_for(
                self.generate_image(type=GreetingType.leave, member=member), timeout=5
            )
            file = discord.File(buf, filename="left.png")
            embed = discord.Embed(
                description=message,
                color=discord.Color.red(),
            )
            embed.set_image(url="attachment://left.png")
            embed.set_footer(text=f"{member.guild.name} • Member #{member.guild.member_count}")
            await channel.send(embed=embed, file=file)
        except asyncio.TimeoutError:
            await channel.send(content=message)
        except Exception:
            # image generation/send failed - don't let a bad leave image break the leave flow
            traceback.print_exc()
            await channel.send(content=message)


async def setup(bot):
    await bot.add_cog(Greeting(bot))