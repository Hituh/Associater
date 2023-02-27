import datetime
import nextcord
from nextcord.ext import commands, tasks
from nextcord import SlashOption
import re

import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
SERVER_ID = int(os.getenv('TESTSERVER_ID'))

class ExtrasCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.members_list = None
        self.guild = None
        self.update_members.start()
    
    @tasks.loop(seconds=60)
    async def update_members(self):
        await self.bot.wait_until_ready()
        self.guild = self.bot.get_guild(SERVER_ID)
        self.members_list = self.guild.members
    
    async def _get_members_by_id(self, value):
        ids_list = re.findall(r'\b\d{18}\b', re.sub(r'[<@>}]', '', value))
        return [self.guild.get_member(int(id)) for id in ids_list]
    
    # Takes amount of minutes and returns formatted string
    def format_duration(self, minutes):
        if minutes == 1:
            return "1 minute"
        if minutes == 5:
            return "5 minutes"
        if minutes == 10:
            return "10 minutes"
        if minutes == 60:
            return "1 hour"
        if minutes == 1440:
            return "1 day"
        if minutes == 10080:
            return "1 week"

    @nextcord.slash_command(description="Mutes selected members", guild_ids=[SERVER_ID], default_member_permissions=8)
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
        print(f'{interaction.user} has used custom_timeout in {interaction.channel} at {datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")} UTC\nInteraction message : {interaction.data}')

        await self.bot.wait_until_ready()
        m_list = await self._get_members_by_id(users)
        
        mutes_message, response_message = ''
        for member in m_list:
            try:
                await member.edit(reason=reason, timeout=datetime.timedelta(minutes=duration))
                response_message +=f'{member.mention} has been timed out.\n'
                mutes_message +=f'{member.mention}, '
            except:
                response_message += f"Couldn't timeout {member.mention}. The user is administrator or has higer perms than the bot.\n"
                continue
            
        mutes_message += f"you have been timed out by {interaction.user.mention}, for {self.format_duration(duration)}. Reason: {reason}"
        mute_channel = self.guild.get_channel(SERVER_ID)
        await mute_channel.send(mutes_message)
        await interaction.response.send_message(response_message, ephemeral=True, delete_after=15)
            
    
    