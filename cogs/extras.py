import datetime
import nextcord
from nextcord.ext import commands, tasks
from nextcord import SlashOption
import re

import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

class ExtrasCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.members_list = None
        self.guild = None
        self.update_members.start()
    
    
    @tasks.loop(seconds=60)
    async def update_members(self):
        await self.bot.wait_until_ready()
        self.guild = self.bot.get_guild(int(os.getenv('TESTSERVER_ID')))
        self.members_list = self.guild.members
    
    async def _get_members_by_id(self, value):
        ids_list = re.findall(r'\b\d{18}\b', re.sub(r'[<@>}]', '', value))
        return [self.guild.get_member(int(id)) for id in ids_list]
      
    @nextcord.slash_command(description="Mutes selected members", guild_ids=[int(os.getenv('TESTSERVER_ID'))], default_member_permissions=8)
    async def custom_timeout(
        self,
        interaction: nextcord.Interaction,
        users: str = SlashOption(description="User or users to timeout"),
        duration: int = SlashOption(description="How long they should be timed out for", choices={
            '60 Seconds': 1,
            '5 Minutes': 5,
            "10 Minutes": 10,
            "60 Minutes": 60,
            "1 Day": 1440,
            "1 Week" : 10080
        }),
        reason: str = SlashOption(description="The reason for timeout") 
    ):
        await self.bot.wait_until_ready()
        m_list = await self._get_members_by_id(users)
        for member in m_list:
            try:
                await member.edit(reason=reason, timeout=datetime.timedelta(minutes=duration))
            except:
                print(f"Couldn't timeout {member.name}. Probably member is administrator or has higer perms than the bot itself.")
        
    @nextcord.slash_command(description="extras cog test command")
    async def extras_test(self, interaction : nextcord.Interaction):
        print(self.members_list)
            
    
    