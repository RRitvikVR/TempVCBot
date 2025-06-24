import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import json

#BOT SETUP
intents = discord.Intents.default()
intents.voice_states = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

#DATA STORAGE
CONFIG_FILE = "config.json"

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f: return json.load(f)
    except FileNotFoundError: return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f: json.dump(config, f, indent=4)

config = load_config()
temp_channels = {}  # {channel_id: user_id}

#CORE LOGIC HELPER FUNCTION

async def create_user_channel(interaction_or_member, guild):
    """A centralized function to create a temporary voice channel."""
    user = interaction_or_member if isinstance(interaction_or_member, discord.Member) else interaction_or_member.user
    
    #Check if the user already owns a channel
    if user.id in temp_channels.values():
        if isinstance(interaction_or_member, discord.Interaction):
            await interaction_or_member.response.send_message("You already have a temporary voice channel.", ephemeral=True)
        # If triggered by voice state, we just ignore it silently.
        return

    #Check if setup has been run correctly
    if str(guild.id) not in config or not isinstance(config[str(guild.id)], dict):
        if isinstance(interaction_or_member, discord.Interaction):
            await interaction_or_member.response.send_message("The server admin needs to run `/setup` first.", ephemeral=True)
        return
        
    category_id = config[str(guild.id)].get("category_id")
    category = guild.get_channel(category_id)

    if not category:
        if isinstance(interaction_or_member, discord.Interaction):
            await interaction_or_member.response.send_message("Error: The configured category is missing. Please ask an admin to run `/setup`.", ephemeral=True)
        return

    try:
        new_channel = await category.create_voice_channel(name=f"{user.display_name}'s Channel")
        temp_channels[new_channel.id] = user.id

        await new_channel.set_permissions(guild.default_role, connect=False)
        if user != guild.owner:
            await new_channel.set_permissions(user, connect=True)

        #If triggered by command, respond to the command
        if isinstance(interaction_or_member, discord.Interaction):
            await interaction_or_member.response.send_message(f"Created channel `{new_channel.name}`! Check your DMs for options.", ephemeral=True)
        
        #Move user to the new channel
        if user.voice:
             await user.move_to(new_channel)
        
        #Always send DM options
        bot.loop.create_task(send_dm_options(user, new_channel))
        
    except discord.Forbidden:
        if isinstance(interaction_or_member, discord.Interaction):
            await interaction_or_member.response.send_message("❌ I lack permissions to create channels in the designated category.", ephemeral=True)


#EVENTS

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    print("------")


@bot.event
async def on_voice_state_update(member, before, after):
    """Handles both Join-to-Create and auto-deletion of empty channels."""
    #Deletion Logic 
    if before.channel and before.channel.id in temp_channels:
        if len(before.channel.members) == 0:
            await asyncio.sleep(5)
            if len(before.channel.members) == 0:
                print(f"Deleting empty channel: {before.channel.name}")
                await before.channel.delete(reason="Temporary channel empty")
                del temp_channels[before.channel.id]

    #Join to Create Logic
    guild_id_str = str(member.guild.id)
    if after.channel and guild_id_str in config and isinstance(config[guild_id_str], dict):
        creator_channel_id = config[guild_id_str].get("creator_channel_id")
        if after.channel.id == creator_channel_id:
            await create_user_channel(member, member.guild)

#SLASH COMMANDS

@bot.tree.command(name="setup", description="[Admin Only] Configures the category for temporary channels.")
@app_commands.checks.has_permissions(manage_channels=True)
async def setup(interaction: discord.Interaction):
    guild = interaction.guild
    category_name = "Temporary Channels"
    creator_channel_name = "➕ Create VC"
    
    bot_permissions = discord.PermissionOverwrite(manage_channels=True, manage_roles=True, move_members=True)

    try:
        # Find or create the main category
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            overwrites = {guild.me: bot_permissions}
            category = await guild.create_category(name=category_name, overwrites=overwrites)
        else:
            await category.set_permissions(guild.me, overwrite=bot_permissions)

        # Find or create the creator voice channel
        creator_channel = discord.utils.get(category.voice_channels, name=creator_channel_name)
        if not creator_channel:
            creator_channel = await category.create_voice_channel(name=creator_channel_name)

        # Save configuration
        config[str(guild.id)] = {
            "category_id": category.id,
            "creator_channel_id": creator_channel.id
        }
        save_config(config)

        await interaction.response.send_message(f"✅ Setup complete. The `{category_name}` category and `{creator_channel_name}` channel are ready.", ephemeral=True)
    
    except discord.Forbidden:
        await interaction.response.send_message("❌ I lack server-wide permissions to create or manage categories. Please check my role permissions.", ephemeral=True)

@bot.tree.command(name="createvc", description="Creates a private voice channel just for you.")
async def createvc(interaction: discord.Interaction):
    """Command-based entry point for channel creation."""
    await create_user_channel(interaction, interaction.guild)


@bot.tree.command(name="invite", description="Invites a user to your temporary voice channel.")
@app_commands.describe(user_to_invite="The person you want to invite")
async def invite(interaction: discord.Interaction, user_to_invite: discord.Member):
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message("You're not in a voice channel.", ephemeral=True); return
    
    channel = interaction.user.voice.channel
    if channel.id in temp_channels and temp_channels[channel.id] == interaction.user.id:
        await channel.set_permissions(user_to_invite, connect=True, reason=f"Invited by {interaction.user.name}")
        await interaction.response.send_message(f"✅ Invited {user_to_invite.mention} to `{channel.name}`.", ephemeral=True)
    else:
        await interaction.response.send_message("This isn't your temporary channel.", ephemeral=True)

@bot.tree.command(name="kick", description="Kicks a user from your temporary voice channel.")
@app_commands.describe(user_to_kick="The person you want to kick")
async def kick(interaction: discord.Interaction, user_to_kick: discord.Member):
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message("You're not in a voice channel.", ephemeral=True); return
        
    channel = interaction.user.voice.channel
    if channel.id in temp_channels and temp_channels[channel.id] == interaction.user.id:
        if user_to_kick == interaction.guild.owner:
            await interaction.response.send_message("The server owner cannot be kicked.", ephemeral=True); return
        if user_to_kick in channel.members:
            await user_to_kick.move_to(None)
            await interaction.response.send_message(f"✅ Kicked {user_to_kick.mention} from `{channel.name}`.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{user_to_kick.mention} is not in this channel.", ephemeral=True)
    else:
        await interaction.response.send_message("This isn't your temporary channel.", ephemeral=True)


async def send_dm_options(member, channel):
    try:
        embed = discord.Embed(title=f"Channel Controls for `{channel.name}`", color=discord.Color.green())
        embed.add_field(name="📢 Public", value="Let anyone join", inline=True)
        embed.add_field(name="🔒 Private", value="Make it invite-only", inline=True)
        embed.add_field(name="🔢 Set Limit", value="Set a user limit", inline=True)
        
        dm = await member.create_dm()
        msg = await dm.send(embed=embed)
        await msg.add_reaction("📢"); await msg.add_reaction("🔒"); await msg.add_reaction("🔢")

        def check(reaction, user):
            return user == member and reaction.message.id == msg.id and str(reaction.emoji) in ["📢", "🔒", "🔢"]
        
        while True:
            try:
                reaction, user = await bot.wait_for("reaction_add", timeout=600.0, check=check)
                if not channel.guild or not channel.guild.get_channel(channel.id):
                    await dm.send("Your channel no longer exists."); return
                
                if str(reaction.emoji) == "📢":
                    await channel.set_permissions(channel.guild.default_role, connect=True)
                    await dm.send("Your channel is now public.")
                elif str(reaction.emoji) == "🔒":
                    await channel.set_permissions(channel.guild.default_role, connect=False)
                    await dm.send("Your channel is now private.")
                elif str(reaction.emoji) == "🔢":
                    await dm.send("What user limit should I set? (Enter 0 for unlimited)")
                    def limit_check(m):
                        return m.author == member and m.channel == dm and m.content.isdigit()
                    
                    try:
                        limit_msg = await bot.wait_for("message", timeout=30.0, check=limit_check)
                        limit = int(limit_msg.content)
                        await channel.edit(user_limit=limit)
                        await dm.send(f"User limit set to `{limit if limit > 0 else 'unlimited'}`.")
                    except asyncio.TimeoutError: await dm.send("You took too long.")
                await msg.remove_reaction(reaction.emoji, user)
            except asyncio.TimeoutError:
                await msg.edit(content="Controls have expired.", embed=None); break
    except discord.Forbidden: pass

bot.run("INSERT_TOKEN_HERE")
