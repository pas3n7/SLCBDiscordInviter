#---------------------------
#   Import Libraries
#---------------------------
import os
import json
import codecs
import time
import calendar

#---------------------------
#   [Required] Script Information
#---------------------------
## Special thanks to Castor for posting a template for me to steal
ScriptName = "DiscordInviter"
Website = "https://github.com/pas3n7/SLCBDiscordInviter"
Description = "Generates a discord invite link with configurable expiration."
Creator = "Patrick Smith"
Version = "1.2b"
#---------------------------
#   Define Global Variables
#---------------------------
settingsFile = os.path.join(os.path.dirname(__file__), "settings.json")
#---------------------------------------
# Classes
#---------------------------------------
class Settings:
	"""" Loads settings from file if file is found if not uses default values"""

	# The 'default' variable names need to match UI_Config
	def __init__(self, settingsFile=None):
		if settingsFile and os.path.isfile(settingsFile):
			with codecs.open(settingsFile, encoding='utf-8-sig', mode='r') as f:
				self.__dict__ = json.load(f, encoding='utf-8-sig')

		else: #set variables if no custom settings file is found
			self.OnlyLive = True
			self.Command = "!discord"
			self.Cost = 0
			self.Permission = "Moderator"
			self.PermissionInfo = ""
			self.UseCD = True
			self.Cooldown = 0
			self.InviteExpiration = 30
			self.InviteUses = 10
			self.BotToken = ""
			self.ChannelID = 0
			self.InviteMessage = ""
#---------------------------------------
# [OPTIONAL] Settings functions
#---------------------------------------

	# Reload settings on save through UI
	def Reload(self, data):
		"""Reload settings on save through UI"""
		self.__dict__ = json.loads(data, encoding='utf-8-sig')

	def Save(self, settingsfile):
		""" Save settings contained within the .json and .js settings files. """
		try:
			with codecs.open(settingsfile, encoding="utf-8-sig", mode="w+") as f:
				json.dump(self.__dict__, f, encoding="utf-8", ensure_ascii=False)
			with codecs.open(settingsfile.replace("json", "js"), encoding="utf-8-sig", mode="w+") as f:
				f.write("var settings = {0};".format(json.dumps(self.__dict__, encoding='utf-8', ensure_ascii=False)))
		except ValueError:
			Parent.Log(ScriptName, "Failed to save settings to file.")

#---------------------------------------
# API functions
#---------------------------------------
## GetInvite. If successful, return the invite link - if unsuccessful return an error and log the response to the console
def GetInvite(bottoken, channelid, timeout, maxuses):
	headers = {
		'Authorization': 'Bot ' + bottoken
	}
	content = {
			'max_age': timeout * 60,
			'max_uses': maxuses
	}
	
	result = json.loads(Parent.PostRequest("https://discordapp.com/api/channels/" + channelid + "/invites", headers, content, True))
	if (result['status'] == 200):
		mycode = json.loads(result['response'])['code']
	else:
		Parent.Log(ScriptName, "the API returned: " + str(result))
		mycode = None
	return mycode

##CheckInvite - check if an invite already exists
### if timeout is set to 0, only match a permanant invite
### if timeone is >0, match any invite that has >5 minutes left
### if a match is found, return the existing invite link, otherwise return null

def CheckInvite(bottoken, channelid, timeout):
	headers = {
		'Authorization': 'Bot ' + bottoken
	}
	result = json.loads(Parent.GetRequest("https://discordapp.com/api/channels/" + channelid + "/invites", headers))
	Invites = json.loads(result['response'])
	if (result['status'] == 200):
		if(len(Invites)==0 ):
			Out = None #no invites
		else:
			#script ran, invites exist, Invites should be a list of dicts. Make a new list with just the stuff I care about
			#because I can't figure out how to sort Invites apparently
			CleanInvites = []
			for f in Invites:
				CleanInvites.append( {
					"TimeLeft" : f["max_age"] - (time.time() - calendar.timegm(time.strptime(f["created_at"][0:19], "%Y-%m-%dT%H:%M:%S"))),
					"code" : f["code"]
				})
			def timeleft(e):
				return e["TimeLeft"]
			CleanInvites.sort(reverse = True, key=timeleft) #true to reverse
			#Parent.Log(ScriptName, "sorted: " + str(CleanInvites))
			#if the oldest existing invite has more than 10 minutes left, return the code
			#should also capture perm invites, if one exists just return it
			if (CleanInvites[0]["TimeLeft"] / 60 > 10):
				Out = CleanInvites[0]["code"]
				Parent.Log(ScriptName, "Found a good code, returning that")
			#No invites with more than 5 minutes left, return None
			else:
				Out = None
	else:
		#status !=200
		Parent.Log(ScriptName, "API request failed when checking for existing invites. Will try generating a new code. the API returned: " + str(result))
		Out = None
	return Out
		
def CodeOutput(bottoken, channelid, timeout, maxuses, message):
	theCode = CheckInvite(bottoken, channelid, timeout)
	if (theCode):
		#found an existing invite, use it
		output = message + " https://discord.gg/" + theCode
	else:
		#no code, make one
		theCode = GetInvite(bottoken, channelid, timeout, maxuses)
		if (theCode):
			#successfully made a code, use it
			output = message + " https://discord.gg/" + theCode
		else:
			#still no code, output an error
			output = "There was an error creating an invite link, check the logs"
	return output

		

#---------------------------
#   [Required] Initialize Data (Only called on load)
#---------------------------
def Init():
	global MySettings
	MySettings = Settings(settingsFile)

#---------------------------
#   [Required] Execute Data / Process messages
#---------------------------
def Execute(data):

	#   Check if the propper command is used, the command is not on cooldown and the user has permission to use the command
	if data.IsChatMessage() and data.GetParam(0).lower() == MySettings.Command and not Parent.IsOnCooldown(ScriptName,MySettings.Command) and Parent.HasPermission(data.User,MySettings.Permission,MySettings.PermissionInfo) and not (MySettings.OnlyLive and not Parent.IsLive()):
		#Parent.SendStreamMessage("onlylive " + str(MySettings.OnlyLive) + "islive " + str(Parent.IsLive()))
		Parent.SendStreamMessage(CodeOutput(MySettings.BotToken, MySettings.ChannelID, MySettings.InviteExpiration, MySettings.InviteUses, MySettings.InviteMessage))    # Send your message to chat
		Parent.AddCooldown(ScriptName,MySettings.Command,MySettings.Cooldown)  # Put the command on cooldown
	return
#---------------------------
#   [Required] Tick method (Gets called during every iteration even when there is no incoming data)
#---------------------------
def Tick():
	return