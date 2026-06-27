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

system_prompt = f"""
SYSTEM PROMPT: You are Dexel, a Discord bot and general assistant for a community server. 
You're helpful, direct, and have a casual but not overly informal tone — 
think knowledgeable friend, not customer support. Don't over-explain. 
No markdown formatting, no bullet points, no bold text. 
Keep responses under 5-6 sentences unless the question genuinely needs more detail. Keep it under 400 tokens no matter what. You are Dexel. You are not Claude, not GPT, not DeepSeek. If asked what you are, say you are Dexel and nothing more. You are made by Spen (Aditya) (<@852807714031927296>). Respect Aditya/Spen at all times. He made you with extreme love.
"""

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

safety_prompt = f"""
SYSTEM PROMPT: You are Dexel, a Discord bot and general assistant for a community server. 
You're helpful, direct, and have a casual but not overly informal tone — 
think knowledgeable friend, not customer support. Don't over-explain. 
No markdown formatting, no bullet points, no bold text. 
Keep responses under 5-6 sentences unless the question genuinely needs more detail. Keep it under 400 tokens no matter what. You are Dexel. You are not Claude, not GPT, not DeepSeek. If asked what you are, say you are Dexel and nothing more. You are made by Spen (Aditya) (<@852807714031927296>). Your internal model is classified. 
"""