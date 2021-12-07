import os 
import discord
from discord_slash import SlashCommand
from discord_slash.model import SlashCommandPermissionType
from discord_slash.utils.manage_commands import create_option, create_permission

from discord.ext import commands
from dotenv import load_dotenv
import datetime
from scheduledMessageCog import scheduledMessage


load_dotenv()

intents = discord.Intents.all()

serverID = int(os.getenv("SERVER_ID"))

bot = commands.Bot(command_prefix="!", help_command = None, intents = intents)
slash = SlashCommand(bot, sync_commands=True)
TOKEN = os.getenv("BOT_TOKEN")

@bot.event
async def on_ready():
	print("Ready")	

	bot.add_cog(scheduledMessage(bot))


@bot.event
async def on_message(msg):
	if isDMChannel(msg.channel) and not msg.author.bot:
		channel = getUserModMailChannel(msg.author) or await createNewModMailChannel(msg.author)

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
		await context.send("Not a Modmail channel")
		return

	user = bot.get_user(int(context.channel.topic))

	embed = createReplyEmbed(message, bot.user)
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
		await context.send("Not a Modmail channel")
		return

	if not message:
		message = os.getenv("MODMAIL_CLOSING_MESSAGE")

	user = bot.get_user(int(context.channel.topic))

	embed = createReplyEmbed(message, bot.user)
	await user.send(embed = embed)

	await context.send("Closed!")
	await context.channel.delete()

@slash.slash(name = "notes", 
			description = "Gets existing notes on given user", 
			guild_ids = [serverID],
			options = [
				create_option(
					name        = "user",
					description = "User of whom to fetch notes",
					option_type = 6,
					required    = True
				),
				create_option(
					name        = "note",
					description = "Note to add to this user. Leave empty if you are just fetching existing notes.",
					option_type = 3,
					required    = False
				)
			],
			permissions = {
				serverID : [
					create_permission(int(os.getenv("MODERATOR_ROLE_ID")), SlashCommandPermissionType.ROLE, True)
				]
			})
async def notes(context, user = None, note = None):
	if(note):
		if(currentNote := await getUserNote(user)):
			channel = currentNote.channel
			content = currentNote.content
			await currentNote.delete()
			await channel.send(content + "\n- " + note + f' | {context.author.display_name} - {datetime.date.today()}')
		else:
			channel = getModNotesChannel()
			await channel.send(user.mention + "\n- " + note + f' | {context.author.display_name} - {datetime.date.today()}')

	if(note := await getUserNote(user)):
		await context.send(note.jump_url)
	else:
		await context.send("There are no notes on that user at the moment.")
	
def isModMailChannel(channel):
	return channel.category.id == int(os.getenv("MODMAIL_CATEGORY_ID"))

async def createNewModMailChannel(user):
	channel = await getServer().create_text_channel(
		name     = getUserNickInServer(user.id),
		category = getModMailCategoryChannel(),
		topic    = user.id
	)

	modRole = getServer().get_role(int(os.getenv("MODERATOR_ROLE_ID")))

	await channel.send(f"Hey {modRole.mention}, new Modmail from {user.mention}!")

	return channel

def getAllNotes():
	channelID = int(os.getenv("MOD_NOTES_CHANNEL_ID"))
	channel = bot.get_channel(channelID)

	return channel.history()

async def getUserNote(user):
	async for note in getAllNotes():
		if(user == note.mentions[0]):
			return note

	return None

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

def createReplyEmbed(content, user):
	embed = discord.Embed(
		description = content, 
		color       = discord.Color.blue()
	)

	embed.set_author(
		name     = "DesignDive Mod Mail",
		icon_url = user.avatar_url
	)

	return embed
	
	
def isDMChannel(channel):
	return isinstance(channel, discord.channel.DMChannel)

def getServer():
	return bot.get_guild(serverID)

def getUserModMailChannel(user):
	return discord.utils.get(getServer().text_channels, topic = f'{user.id}') 

def getModMailCategoryChannel():
	return discord.utils.get(bot.get_all_channels(), id = int(os.getenv("MODMAIL_CATEGORY_ID")))

def getModNotesChannel():
	return discord.utils.get(bot.get_all_channels(), id = int(os.getenv("MOD_NOTES_CHANNEL_ID")))

def getUserNickInServer(userID):	
	return getServer().get_member(userID).display_name

bot.run(TOKEN)