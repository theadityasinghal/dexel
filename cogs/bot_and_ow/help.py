import discord
from discord import app_commands
from discord.ext import commands


# ── Command metadata ───────────────────────────────────────────────────────────

COMMANDS: dict[str, dict] = {
    "slowmode": {
        "category": "Moderation",
        "name": "/slowmode",
        "description": (
            "View or set the slowmode for a channel. "
            "Supports human-readable durations like `30s`, `5m`, `1h`. "
            "Can auto-remove after a set time via a background task."
        ),
        "usage": "/slowmode [seconds] [channel] [remove_after]",
        "parameters": [
            ("`seconds`",      "Optional", "Duration string (`30s`, `5m`, `1h`). If omitted, shows the current slowmode of the target channel."),
            ("`channel`",      "Optional", "Target channel. Defaults to the channel the command is run in."),
            ("`remove_after`", "Optional", "Auto-removes the slowmode after this duration. Runs as a background task."),
        ],
        "subcommands": None,
        "permissions": "Manage Channels",
        "notes": (
            "The action is logged to Discord's audit log with the user's tag and ID. "
            "If the bot lacks permissions in the target channel it catches the error gracefully "
            "and replies with an explanation."
        ),
    },
    "counting": {
        "category": "Games",
        "name": "/counting",
        "description": (
            "A counting game for your server. Members count up from 0 in the configured channel. "
            "Wrong numbers, duplicate counts, or non-numeric messages are rejected. "
            "Tracks an all-time high score and per-user leaderboard."
        ),
        "usage": "/counting <subcommand>",
        "parameters": None,
        "subcommands": [
            ("`setup <channel>`", "Set the channel where the counting game runs. The bot immediately begins listening there."),
            ("`reset`",           "Reset the current count back to 0. The all-time high score and leaderboard are kept."),
        ],
        "permissions": "Manage Guild",
        "notes": (
            "Once a channel is configured the bot listens via `on_message` — no command needed to play. "
            "Milestone reactions and high-score announcements are handled automatically."
        ),
    },
    "about": {
        "category": "Bot",
        "name": "/about",
        "description": (
            "Shows information about Dexel: invite link, support server, owner, "
            "server count, total user count, WebSocket ping, and uptime."
        ),
        "usage": "/about",
        "parameters": None,
        "subcommands": None,
        "permissions": "None",
        "notes": None,
    },
    "ping": {
        "category": "Bot",
        "name": "/ping",
        "description": "Shows the bot's current WebSocket latency in milliseconds.",
        "usage": "/ping",
        "parameters": None,
        "subcommands": None,
        "permissions": "None",
        "notes": None,
    },
    "help": {
        "category": "Bot",
        "name": "/help",
        "description": (
            "Browse all of Dexel's commands by category, or look up detailed info on a specific command. "
            "Without an argument it shows an interactive category menu. "
            "With a command name it shows full usage, parameters, and permission details."
        ),
        "usage": "/help [command]",
        "parameters": [
            ("`command`", "Optional", "A specific command to look up. Picks from a dropdown list — no free-text input."),
        ],
        "subcommands": None,
        "permissions": "None",
        "notes": "Viewing help for a command never requires you to hold the permissions that command needs.",
    },
    "ai": {
        "category": "AI",
        "name": "/ai",
        "description": (
            "AI-powered commands for your server. "
            "Set up a dedicated channel for context-aware conversations, "
            "or send one-off prompts directly with `/ai chat`."
        ),
        "usage": "/ai <subcommand>",
        "parameters": None,
        "subcommands": [
            ("`setup [channel] [pre_prompt]`", (
                "Configure the AI channel and pre-prompt. Both params are optional — "
                "calling it with no args shows the current config. Requires **Manage Guild**."
            )),
            ("`chat <prompt>`", (
                "Send a one-off prompt to the AI. No setup or history — each call is independent."
            )),
        ],
        "permissions": "Manage Guild (setup only)",
        "notes": (
            "Once a channel is set via `setup`, the bot listens via `on_message` and maintains "
            "a per-guild sliding window of the last 20 messages as context. "
            "The pre-prompt is always injected with a distrust caveat. "
            "`/ai chat` is stateless — it never reads or writes conversation history."
        ),
    },
}


# ── Category page content ──────────────────────────────────────────────────────

CATEGORIES: dict[str, tuple[str, str]] = {
    "moderation": (
        "🔨 Moderation",
        (
            "Commands to manage your server's settings and behaviour.\n\n"
            "`/slowmode` — View or set channel slowmode. Requires **Manage Channels**.\n"
            "> Supports durations like `30s`, `5m`, `1h`. Can auto-remove after a set time.\n"
        ),
    ),
    "games": (
        "🎮 Games",
        (
            "Interactive games for your community.\n\n"
            "`/counting setup` — Configure the counting channel. Requires **Manage Guild**.\n"
            "`/counting reset` — Reset the count to 0. Requires **Manage Guild**.\n"
            "> Once set up, members count in the configured channel. "
            "The bot tracks all-time high scores and per-user leaderboards automatically."
        ),
    ),
    "bot": (
        "🤖 Bot",
        (
            "Meta commands about Dexel itself.\n\n"
            "`/about` — Bot info: invite link, support server, owner, uptime, server + user counts.\n"
            "`/ping` — WebSocket latency.\n"
            "`/help` — This command. Browse categories or look up a specific command."
        ),
    ),
    "ai": (
        "🧠 AI",
        (
            "AI-powered commands.\n\n"
            "`/ai setup` — Configure a channel for context-aware AI chat. Requires **Manage Guild**.\n"
            "> Maintains a sliding 20-message history per server. Supports custom pre-prompts.\n\n"
            "`/ai chat` — One-off AI prompt with no setup or history needed."
        ),
    ),
    "server": (
        "🏠 Server",
        "Nothing here yet — coming soon.",
    ),
    "utility": (
        "🛠️ Utility",
        "Nothing here yet — coming soon.",
    ),
}


# ── UI ─────────────────────────────────────────────────────────────────────────

class CategorySelect(discord.ui.Select):
    def __init__(self) -> None:
        options = [
            discord.SelectOption(label="🔨 Moderation", value="moderation"),
            discord.SelectOption(label="🎮 Games",       value="games"),
            discord.SelectOption(label="🤖 Bot",         value="bot"),
            discord.SelectOption(label="🧠 AI",          value="ai"),
            discord.SelectOption(label="🏠 Server",      value="server"),
            discord.SelectOption(label="🛠️ Utility",     value="utility"),
        ]
        super().__init__(placeholder="Browse a category...", options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        title, desc = CATEGORIES[self.values[0]]
        embed = discord.Embed(title=title, description=desc, color=discord.Color.blurple())
        embed.set_footer(text="Dexel Help  •  /help <command> for full details")
        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(discord.ui.View):
    def __init__(self, author_id: int) -> None:
        super().__init__(timeout=120)
        self.author_id = author_id
        self.add_item(CategorySelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Not your menu.", ephemeral=True)
            return False
        return True


# ── Cog ────────────────────────────────────────────────────────────────────────

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ── embed builders ────────────────────────────────────────────────────────

    def _home_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="Dexel Help",
            description=(
                "Use the dropdown below to browse commands by category, "
                "or run `/help <command>` to look up a specific command.\n\n"
                "🔨 **Moderation** — Channel and server management\n"
                "🎮 **Games** — Interactive server games\n"
                "🤖 **Bot** — Info and meta commands\n"
                "🧠 **AI** — AI chat features\n"
                "🏠 **Server** — Coming soon\n"
                "🛠️ **Utility** — Coming soon"
            ),
            color=discord.Color.blurple(),
        )
        embed.set_footer(text="Dexel Help  •  /help <command> for full details")
        return embed

    def _command_embed(self, key: str) -> discord.Embed:
        cmd = COMMANDS[key]
        embed = discord.Embed(
            title=cmd["name"],
            description=cmd["description"],
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Category",    value=cmd["category"],          inline=True)
        embed.add_field(name="Permissions", value=cmd["permissions"],       inline=True)
        embed.add_field(name="Usage",       value=f"`{cmd['usage']}`",      inline=False)

        if cmd["parameters"]:
            lines = "\n".join(
                f"{name} — **{req}**\n{desc}"
                for name, req, desc in cmd["parameters"]
            )
            embed.add_field(name="Parameters", value=lines, inline=False)

        if cmd["subcommands"]:
            lines = "\n".join(f"{name}\n{desc}" for name, desc in cmd["subcommands"])
            embed.add_field(name="Subcommands", value=lines, inline=False)

        if cmd["notes"]:
            embed.add_field(name="Notes", value=cmd["notes"], inline=False)

        embed.set_footer(text="Dexel Help")
        return embed

    # ── command ───────────────────────────────────────────────────────────────

    @app_commands.command(name="help", description="Browse Dexel's commands or look up a specific one.")
    @app_commands.describe(command="A specific command to look up.")
    @app_commands.choices(command=[
        app_commands.Choice(name="slowmode", value="slowmode"),
        app_commands.Choice(name="counting", value="counting"),
        app_commands.Choice(name="about",    value="about"),
        app_commands.Choice(name="ping",     value="ping"),
        app_commands.Choice(name="help",     value="help"),
        app_commands.Choice(name="ai",       value="ai"),
    ])
    async def help_command(
        self,
        interaction: discord.Interaction,
        command: str | None = None,
    ) -> None:
        if command:
            await interaction.response.send_message(
                embed=self._command_embed(command),
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                embed=self._home_embed(),
                view=HelpView(interaction.user.id),
                ephemeral=True,
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Help(bot))