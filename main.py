import os 
import discord
from discord_slash import SlashCommand
from discord_slash.model import SlashCommandPermissionType
from discord_slash.utils.manage_commands import create_option, create_permission

from discord.ext import commands
from dotenv import load_dotenv


load_dotenv()

intents = discord.Intents.all()

serverID = int(os.getenv("SERVER_ID"))

bot = commands.Bot(command_prefix="!", help_command = None, intents = intents)
slash = SlashCommand(bot, sync_commands=True)
TOKEN = os.getenv("BOT_TOKEN")

@bot.event
async def on_ready():
	print("Ready")		

@bot.event
async def on_message(msg):
	if isDMChannel(msg.channel) and not msg.author.bot:
		authorID = msg.author.id 
		channel = getUserModMailChannel(authorID) or await createNewModMailChannel(authorID)

		await channel.send(embed = createModMailEmbed(msg.content, msg.author))

@slash.slash(name = "reply", 
			description = "Replies to the sender of this ModMail with the provided message", 
			guild_ids = [serverID],
			options = [
				create_option(
					name        = "message",
					description = "Message to be sent as a reply",
					option_type = 3,
					required    = True
				)
			],
			permissions = {
				serverID : [
					create_permission(int(os.getenv("MODERATOR_ROLE_ID")), SlashCommandPermissionType.ROLE, True)
				]
			})
async def reply(context, message):
	if not isModMailChannel(context.channel):
		return

	user = bot.get_user(int(context.channel.topic))

	embed = createModMailEmbed(message, bot.user)
	await user.send(embed = embed)
	await context.send(content = "Sent this to the user", embed = embed)

@slash.slash(name = "close", 
			description = "Closes this ticket", 
			guild_ids = [serverID],
			options = [
				create_option(
					name        = "message",
					description = "Closing message to be sent to the user",
					option_type = 3,
					required    = False
				)
			],
			permissions = {
				serverID : [
					create_permission(int(os.getenv("MODERATOR_ROLE_ID")), SlashCommandPermissionType.ROLE, True)
				]
			})
async def close(context, message = None):
	if not isModMailChannel(context.channel):
		return

	if not message:
		message = os.getenv("MODMAIL_CLOSING_MESSAGE")

	user = bot.get_user(int(context.channel.topic))

	embed = createModMailEmbed(message, bot.user)
	await user.send(embed = embed)


moderatorPermissions = {
	serverID : [
		create_permission(int(os.getenv("MODERATOR_ROLE_ID")), SlashCommandPermissionType.ROLE, True)
	]
}
	
def isModMailChannel(channel):
	return channel.category.id == int(os.getenv("MODMAIL_CATEGORY_ID"))

async def createNewModMailChannel(userID):
	channel = await getServer().create_text_channel(
		name     = getUserNickInServer(userID),
		category = getModMailCategoryChannel(),
		topic    = userID
	)

	modRole = getServer().get_role(int(os.getenv("MODERATOR_ROLE_ID")))

	await channel.send(f"New Modmail! {modRole.mention}")

	return channel

def createModMailEmbed(content, user):
	embed = discord.Embed(
		description = content, 
		color       = discord.Color.blue()
	)

	embed.set_author(
		name     = getUserNickInServer(user.id),
		icon_url = user.avatar_url
	)

	return embed
	
def isDMChannel(channel):
	return isinstance(channel, discord.channel.DMChannel)

def getServer():
	return bot.get_guild(serverID)

def getUserModMailChannel(userID):
	return discord.utils.get(getServer().text_channels, topic = f'{userID}') 

def getModMailCategoryChannel():
	return discord.utils.get(bot.get_all_channels(), id = int(os.getenv("MODMAIL_CATEGORY_ID")))

def getUserNickInServer(userID):	
	return getServer().get_member(userID).display_name

bot.run(TOKEN)