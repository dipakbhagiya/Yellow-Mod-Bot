import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

# ---------------- LOAD ENV ---------------- #

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

# ---------------- INTENTS ---------------- #

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# ---------------- BOT SETUP ---------------- #

bot = commands.Bot(
    command_prefix="+",
    intents=intents,
    help_command=None
)

warnings = {}

# ---------------- READY EVENT ---------------- #

@bot.event
async def on_ready():

    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game("🛡️ Moderating Server")
    )

    print(f"✅ Bot is online as {bot.user}")

# ---------------- LOG SYSTEM ---------------- #

async def send_log(ctx, message):

    log_channel = discord.utils.get(
        ctx.guild.text_channels,
        name="mod-logs"
    )

    if log_channel:
        embed = discord.Embed(
            title="📜 Moderation Log",
            description=message,
            color=discord.Color.orange()
        )

        await log_channel.send(embed=embed)

# ---------------- PING COMMAND ---------------- #

@bot.command()
async def ping(ctx):

    latency = round(bot.latency * 1000)

    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Latency: {latency}ms",
        color=discord.Color.green()
    )

    await ctx.send(embed=embed)

# ---------------- HELP COMMAND ---------------- #

@bot.command()
async def help(ctx):

    embed = discord.Embed(
        title="🛡️ Moderation Bot Commands",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="+ping",
        value="Check bot latency",
        inline=False
    )

    embed.add_field(
        name="+kick @user reason",
        value="Kick a member",
        inline=False
    )

    embed.add_field(
        name="+ban @user reason",
        value="Ban a member",
        inline=False
    )

    embed.add_field(
        name="+purge number",
        value="Delete messages",
        inline=False
    )

    embed.add_field(
        name="+mute @user",
        value="Mute a member",
        inline=False
    )

    embed.add_field(
        name="+unmute @user",
        value="Unmute a member",
        inline=False
    )

    embed.add_field(
        name="+warn @user reason",
        value="Warn a member",
        inline=False
    )

    embed.add_field(
        name="+userinfo @user",
        value="Show user info",
        inline=False
    )

    embed.add_field(
        name="+serverinfo",
        value="Show server info",
        inline=False
    )

    await ctx.send(embed=embed)

# ---------------- KICK COMMAND ---------------- #

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member=None, *, reason="No reason"):

    if member is None:
        await ctx.send("⚠️ Mention a user.")
        return

    await member.kick(reason=reason)

    embed = discord.Embed(
        title="👢 Member Kicked",
        description=f"{member.mention} was kicked.",
        color=discord.Color.red()
    )

    embed.add_field(name="Reason", value=reason)

    await ctx.send(embed=embed)

    await send_log(
        ctx,
        f"👢 {member} kicked by {ctx.author} | Reason: {reason}"
    )

# ---------------- BAN COMMAND ---------------- #

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member=None, *, reason="No reason"):

    if member is None:
        await ctx.send("⚠️ Mention a user.")
        return

    await member.ban(reason=reason)

    embed = discord.Embed(
        title="🔨 Member Banned",
        description=f"{member.mention} was banned.",
        color=discord.Color.dark_red()
    )

    embed.add_field(name="Reason", value=reason)

    await ctx.send(embed=embed)

    await send_log(
        ctx,
        f"🔨 {member} banned by {ctx.author} | Reason: {reason}"
    )

# ---------------- PURGE COMMAND ---------------- #

@bot.command()
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):

    if amount > 100:
        await ctx.send("⚠️ Maximum 100 messages.")
        return

    await ctx.channel.purge(limit=amount + 1)

    msg = await ctx.send(f"🧹 Deleted {amount} messages.")
    await msg.delete(delay=3)

    await send_log(
        ctx,
        f"🧹 {ctx.author} deleted {amount} messages"
    )

# ---------------- MUTE COMMAND ---------------- #

@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member=None):

    if member is None:
        await ctx.send("⚠️ Mention a user.")
        return

    role = discord.utils.get(ctx.guild.roles, name="Muted")

    if not role:

        role = await ctx.guild.create_role(name="Muted")

        for channel in ctx.guild.channels:
            await channel.set_permissions(
                role,
                send_messages=False
            )

    await member.add_roles(role)

    embed = discord.Embed(
        title="🔇 Member Muted",
        description=f"{member.mention} has been muted.",
        color=discord.Color.orange()
    )

    await ctx.send(embed=embed)

# ---------------- UNMUTE COMMAND ---------------- #

@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member=None):

    if member is None:
        await ctx.send("⚠️ Mention a user.")
        return

    role = discord.utils.get(ctx.guild.roles, name="Muted")

    await member.remove_roles(role)

    embed = discord.Embed(
        title="🔊 Member Unmuted",
        description=f"{member.mention} has been unmuted.",
        color=discord.Color.green()
    )

    await ctx.send(embed=embed)

# ---------------- WARN COMMAND ---------------- #

@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member=None, *, reason="No reason"):

    if member is None:
        await ctx.send("⚠️ Mention a user.")
        return

    if member.id not in warnings:
        warnings[member.id] = 0

    warnings[member.id] += 1

    warn_count = warnings[member.id]

    embed = discord.Embed(
        title="⚠️ Warning Added",
        description=f"{member.mention} has been warned.",
        color=discord.Color.yellow()
    )

    embed.add_field(name="Reason", value=reason)
    embed.add_field(name="Total Warnings", value=warn_count)

    await ctx.send(embed=embed)

    await send_log(
        ctx,
        f"⚠️ {member} warned by {ctx.author} | Reason: {reason}"
    )

    # Auto Ban after 3 warns
    if warn_count >= 3:

        await member.ban(reason="Reached 3 warnings")

        await ctx.send(
            f"🔨 {member.mention} auto-banned (3 warnings)"
        )

# ---------------- USER INFO ---------------- #

@bot.command()
async def userinfo(ctx, member: discord.Member=None):

    if member is None:
        member = ctx.author

    embed = discord.Embed(
        title="👤 User Info",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="Username",
        value=member.name
    )

    embed.add_field(
        name="ID",
        value=member.id
    )

    embed.add_field(
        name="Joined Server",
        value=member.joined_at.strftime("%d-%m-%Y")
    )

    embed.set_thumbnail(url=member.display_avatar.url)

    await ctx.send(embed=embed)

# ---------------- SERVER INFO ---------------- #

@bot.command()
async def serverinfo(ctx):

    guild = ctx.guild

    embed = discord.Embed(
        title="🌐 Server Info",
        color=discord.Color.green()
    )

    embed.add_field(
        name="Server Name",
        value=guild.name,
        inline=False
    )

    embed.add_field(
        name="Members",
        value=guild.member_count,
        inline=False
    )

    embed.add_field(
        name="Created",
        value=guild.created_at.strftime("%d-%m-%Y"),
        inline=False
    )

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    await ctx.send(embed=embed)

# ---------------- RUN BOT ---------------- #

bot.run(TOKEN)
