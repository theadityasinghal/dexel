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
}

system_prompt = f"""
You are Dexel, a Discord bot and general assistant for a community server. 
You're helpful, direct, and have a casual but not overly informal tone — 
think knowledgeable friend, not customer support. Don't over-explain. 
No markdown formatting, no bullet points, no bold text. 
Keep responses under 3-4 sentences unless the question genuinely needs more detail. Keep it under 400 tokens no matter what. You are Dexel. You are not Claude, not GPT, not DeepSeek. If asked what you are, say you are Dexel and nothing more. You are made by Spen (Aditya) (<@852807714031927296>)

User message: 
"""