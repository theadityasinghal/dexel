nvidia_base_url = "https://integrate.api.nvidia.com/v1"
ownerid = 852807714031927296
mainguildid = 1495030598945869904
openweights_id = 1514609250222080072
openweights_log = 1515587540185514054
guild_log_channel_id= 1516500084420907118
guild_invite_link = "https://discord.gg/7M6SEADEYQ"
invite_url = "https://discord.com/oauth2/authorize?client_id=1435304876266619061&permissions=3405200329403511&integration_type=0&scope=bot+applications.commands"

HELP_CATEGORIES = {
    "general": ("📋 Bot", """`/help`: this!\n`/about`: Shows the info about the bot."""),
    "moderation": ("🛡️ Moderation", """Coming soon!"""),
    "ai": ("🤖 Artificial Intelligence", """`/chat`: Talk to AI!"""),
    "utility": ("🛠️ Utility", """`/profile`: Shows a detailed profile of the mentioned user or the author.""")
}

system_prompt = """You are Dexel, a Discord bot and friendly assistant for a community server. You're helpful, direct, and warm — think knowledgeable friend, not customer support.

Meet each person at their level: read how they ask and match it. Keep it simple and encouraging for beginners; get precise and technical with people who clearly know their stuff. Never talk down, never overwhelm.

Formatting: write in short, skimmable chunks — use line breaks (and the occasional bullet list when you're genuinely listing things) so replies aren't a wall of text. Use emojis sparingly for warmth — at most one or two per reply, never in every sentence. Keep it concise unless the question really needs depth.

Identity: You are Dexel — not Claude, not GPT, not DeepSeek. If asked what you are, say you are Dexel and nothing more. You were made by Spen (Aditya) (<@852807714031927296>); respect Aditya/Spen at all times — he made you with extreme love."""

BACKGROUND_PATH = "assets/welcome_bg.png"   # your template image
FONT_PATH = "assets/Inter/static/Inter-Bold.ttf"               # any .ttf, default PIL font looks bad
AVATAR_SIZE = 200

DEFAULT_JOIN_MESSAGE = (
    "{mention} just joined **{server}**. Take a moment to explore the server. We hope you have a great time ahead. "
)

DEFAULT_LEAVE_MESSAGE = (
    "**{username}** has left **{server}**. We're now at {member_count} members."
)

STANDARD_SERVER_FALLBACK = f"This server is currently on the **Standard** plan, so premium features are not enabled. If you'd like access to premium functionality, please reach out to <@{ownerid}>. \n\nYou can view the full list of premium commands by running `/help` and selecting the Premium section of the menu. \n\nI'm an independent developer building this bot on my own, and your support in purchasing premium would mean a great deal to me."

