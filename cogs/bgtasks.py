import nextcord
import os
import datetime

from nextcord.ext import tasks, commands
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
SERVER_ID = int(os.getenv('TESTSERVER_ID'))

    
class TaskCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.index = 0
        self.archived_delete.start()
        self.bot.loop.create_task(self._get_autorequest_channels())
        self.request_channels = []

    # Finding all autorequest channels in guild. Channels need to have 'autorequest' in their name
    async def _get_autorequest_channels(self):
        if getattr(self.bot, "autorequest_channels_set", False) is False:
            await self.bot.wait_until_ready()
            self.bot.autorequest_channels_set = True
            guild = self.bot.get_guild(SERVER_ID)
            for channel in guild.text_channels:
                if 'autorequest' in channel.name:
                    self.request_channels.append(channel)
                    
    # Every 60 seconds removed archived threads from autorequest channnels
    @tasks.loop(seconds=60)
    async def archived_delete(self):
        await self.bot.wait_until_ready()
        for channel in self.request_channels:
            for thread in channel.threads:
                messages = await thread.history(limit=2, oldest_first=True).flatten()
                recent_message = await thread.history(limit=1, oldest_first=False).flatten()
                timedelta = datetime.datetime.utcnow().date() - recent_message[0].created_at.date()
                days = timedelta.total_seconds()
                

                thread_mark = thread.name[:2]
                if thread_mark == '✔ ' and days >= 3:
                    print(f"{thread.name} has been accepted and hasn't received any messages in past 3 days. Deleting...")
                    await thread.delete()
                if thread_mark == '? ' and days >= 7:
                    print(f"{thread.name} is waiting for approval and hasn't received any messages in past 7 days. Deleting...")
                    await thread.delete()
                if thread_mark == '⚠ ' and days >= 3:
                    print(f"{thread.name} has been denied and hasn't received any messages in past 3 days. Deleting...")
                    await thread.delete()
                if thread_mark != '✔ ' and thread_mark != '? ' and thread_mark != '⚠ ' and days >= 3:
                    print(f"{thread.name} is freshly created and hasn't received any messages in past 3 days. Deleting...")
                    await thread.delete()


