import nextcord
import os

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
            async for thread in channel.archived_threads(private = True):
                print(f"Deleted archived thread : {thread.name}")
                await thread.delete()
