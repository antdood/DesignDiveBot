from discord.ext import tasks, commands
from asyncio import sleep
from zoneinfo import ZoneInfo

import yaml

from pathlib import Path
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import re


class scheduledMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.printer.start()

    def cog_unload(self):
        self.printer.cancel()

    @tasks.loop(seconds=0.0)
    async def printer(self):
        time, messageData = getNextSchedule()
        print("Scheduled Message")
        print(time)
        print(f'{getSecondsUntilSchedule(time)} seconds from now.')
        print(messageData)
        
        await sleep(getSecondsUntilSchedule(time) + 5)
        await self.bot.get_channel(messageData["channel"]).send(messageData["message"])
        print("Sent Message")
        print(time)
        print(messageData)
    
def getFile(path, mode = "r"):
    cdir = Path(__file__).resolve().parent

    return open(cdir / path, mode)

def getRawSchedule():
    with getFile("schedule.yml") as file:
        return yaml.safe_load(file)

def getFormattedSchedule():
    rawSchedule = getRawSchedule()
    return {**formatOneoff(rawSchedule), **formatRecurring(rawSchedule)}

def formatOneoff(rawSchedule):
    now = datetime.now(ZoneInfo("America/New_York"))
    out = {}

    for time, scheduleData in getItemsOrNone(rawSchedule["oneoff"]):
        date = datetime.strptime(time, "%d/%m/%Y %H-%M-%S").replace(tzinfo=ZoneInfo("America/New_York"))
        if (date > now):
            out[date] = scheduleData
    
    return out

def formatRecurring(rawSchedule):
    return {**formatDaily(rawSchedule), **formatWeekly(rawSchedule), **formatMonthly(rawSchedule)}

def formatDaily(rawSchedule):
    now = datetime.now(ZoneInfo("America/New_York"))

    out = {}

    for time, scheduleData in getItemsOrNone(rawSchedule["recurring"]["daily"]):
        nextSchedule = datetime(now.year, now.month, now.day, *getTimesFromString(time)).replace(tzinfo=ZoneInfo("America/New_York"))
        if (nextSchedule < now):
            nextSchedule += timedelta(days = 1)

        out[nextSchedule] = scheduleData

    return out

def formatWeekly(rawSchedule):
    now = datetime.now(ZoneInfo("America/New_York"))

    out = {}  

    # tried to do dict comprehension for this but I didn't even get close before I gave up
    for day, schedules in getItemsOrNone(rawSchedule["recurring"]["weekly"]):
        date = datetime(now.year, now.month, now.day).replace(tzinfo=ZoneInfo("America/New_York")) + timedelta(days = daysUntilWeekday(now, day))
        for time, scheduleData in getItemsOrNone(schedules):
            hours, minutes, seconds = getTimesFromString(time)
            nextSchedule = date.replace(hour = hours, minute = minutes, second = seconds)

            if (nextSchedule < now):
                nextSchedule += timedelta(days = 7)

            out[nextSchedule] = scheduleData

    return out

def formatMonthly(rawSchedule):
    now = datetime.now(ZoneInfo("America/New_York"))

    out = {}

    for date, schedules in getItemsOrNone(rawSchedule["recurring"]["monthly"]):
        date = datetime(now.year, now.month, date).replace(tzinfo=ZoneInfo("America/New_York"))
        for time, scheduleData in getItemsOrNone(schedules):
            hours, minutes, seconds = getTimesFromString(time)
            nextSchedule = date.replace(hour = hours, minute = minutes, second = seconds)

            if (nextSchedule < now):
                nextSchedule += relativedelta(months=+1)

            out[nextSchedule] = scheduleData
        
    return out        

def getItemsOrNone(dictionary):
    if(dictionary):
        return dictionary.items()
    else:
        return []

def daysUntilWeekday(datetime, target):
    return (weekdayToNumber(target) - datetime.weekday() + 7) % 7
        
def weekdayToNumber(weekdayString):
    weekdays = {
        "monday" :    0,
        "tuesday" :   1,    
        "wednesday" : 2,    
        "thursday" :  3,    
        "friday" :    4, 
        "saturday" :  5,     
        "sunday" :    6 
    }

    return weekdays[weekdayString.lower()]

def getTimesFromString(string):
    matches = re.match(r'(\d+)-(\d+)-(\d+)', string)
    return int(matches.group(1)), int(matches.group(2)), int(matches.group(3))

def getNextSchedule():
    return min(getItemsOrNone(getFormattedSchedule()), key = lambda schedule : schedule[0])

def getSecondsUntilSchedule(time):
    now = datetime.now(ZoneInfo("America/New_York"))

    return (time - now).total_seconds()
    
    
    
    