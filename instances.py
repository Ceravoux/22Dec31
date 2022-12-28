from disnake import Activity, ActivityType
from disnake.ext.commands import InteractionBot
from worker import Worker


bot = InteractionBot(activity=Activity(name="/help", type=ActivityType.watching))
worker = Worker(loop=bot.loop, bot=bot)