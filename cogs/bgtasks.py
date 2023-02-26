import nextcord
import asyncpg
import asyncio
import os


from dotenv import load_dotenv
load_dotenv()

request_channels = ['1076824842155860059', '1076824842155860060', '1076824842155860061', '1076824842155860062', '1076824842155860063', '1076824842155860064']

from nextcord.ext import tasks, commands
    
    
class TaskCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.index = 0
        self.archived_delete.start()

    def cog_unload(self):
        self.printer.cancel()

    @tasks.loop(seconds=60)
    async def archived_delete(self):
        await self.bot.wait_until_ready()
        guild = self.bot.get_guild(int(os.getenv('TESTSERVER_ID'))  )
        for channel in guild.channels:
            if str(channel.id) in request_channels:
                async for thread in channel.archived_threads(private = True):
                    print(f"Deleted archived thread : {thread.name}")
                    await thread.delete()


def setup(bot):
    bot.add_cog(TaskCog(bot))
