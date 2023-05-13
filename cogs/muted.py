import datetime
import nextcord
from nextcord.ext import commands, tasks
from nextcord import SlashOption, Interaction
from typing import Optional

from database import database
import re

import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
SERVER_ID = int(os.getenv('TESTSERVER_ID'))

def curr_time():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")

class MutedCog(commands.Cog):
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
        # Regular expression pattern to match 18-digit IDs
        pattern = r'<@(\d{18})>'
        ids_list = re.findall(pattern, value)
        return [self.guild.get_member(int(id)) for id in ids_list]
    
    #Adds suffix to a number
    def ordinal(self, n: int):
        if 11 <= (n % 100) <= 13:
            suffix = 'th'
        else:
            suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
        return str(n) + suffix
    
    # Returns user id. Takes user class or user name as input.

    def _get_user_id(self, value):
        user_id = None
        if len(value[2:-1]) == 18 and value[2:-1].isdigit():
            user_id = value[2:-1]
        if (user_id == None):
            for member in self.guild.members:
                if (member.nick is not None and member.nick == value) or member.name == value:
                    user_id = member.id

        return user_id
    
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

    @nextcord.slash_command(description="Shows info about muted members", guild_ids=[SERVER_ID], default_member_permissions=8)
    async def show_muted_members(
        self,
        interaction: nextcord.Interaction,
        type: str = SlashOption(name='type', description="Type of list", choices={
                                'All': 'all', 'Person': 'person'}),
        name: Optional[str] = SlashOption(
            name='name', description='If previously selected "Person", write their name here')
    ):
        print(f'{interaction.user} has used show_muted_members in {interaction.channel} at {curr_time()} UTC')
        print(f'{interaction.data}')
        await interaction.response.defer(ephemeral=True, with_message=True)

        if type == 'all':
            muted_list = database.get_data('muted', columns='user_id')
            muted_dict = {}
            for item in muted_list:
                key = item[0]
                if key in muted_dict:
                    muted_dict[key] += 1
                else:
                    muted_dict[key] = 1

            message = "**Here's the list of all people that have been muted so far:**\n"

            for id, count in muted_dict.items():
                message += f"<@{id}> - {count}\n"

            if len(message) > 1000:
                for i in range(0, len(message), 1000):
                    em = nextcord.Embed(
                        description=message[i:i+1000],
                        color=0xFFFFFF)
                    await interaction.followup.send(message[i:i+1000], ephemeral=True, delete_after=180)
            else:
                em = nextcord.Embed(
                    description=message,
                    color=0xFFFFFF)
                await interaction.followup.send(message, ephemeral=True, delete_after=180)

        if type == 'person':
            if name is None:
                await interaction.followup.send('When you select "Person", please include their name.', ephemeral=True, delete_after=30)
            else:
                member_id = self._get_user_id(name)
                if member_id is None:
                    await interaction.followup.send('Name was not found in the muted members list. Please try again.', ephemeral=True, delete_after=30)
                    return

                muted_list = database.get_data(
                    'muted', columns='user_id, date, reason, length', where=f"WHERE user_id = {member_id}")
                message = f"**User <@{member_id}> has been muted {len(muted_list)} time(s).**\n**Details:**\n"

                for case in muted_list:
                    message += f"Date: {case[1]}\n     Reason: {case[2]}\n     Length: {(case[3])}\n"

                await interaction.followup.send(message, ephemeral=True, delete_after=30)


    @nextcord.slash_command(description="Shows info about muted members", guild_ids=[SERVER_ID], default_member_permissions=8)
    async def clear_mutes(self,
                          interaction: nextcord.Interaction,
                          name: str = SlashOption(name='name', description='Name of the person you want to remove from muted members')
                          ):
        print(f'{interaction.user} has used clear_mutes in {interaction.channel} at {curr_time()} UTC')
        print(f'{interaction.data}')
        await interaction.response.defer(ephemeral=True, with_message=True)

        member_id = self._get_user_id(name)
        if member_id is None:
            await interaction.followup.send('Name was not found in the muted members list. Please try again.', ephemeral=True, delete_after=30)
            return
        database.delete_data('muted', where=f"WHERE user_id = {member_id}")
        message = f"**Deleted every entry of <@{member_id}> in muted members list**"
        await interaction.followup.send(message, ephemeral=True, delete_after=30)
                                 

    @nextcord.slash_command(description="Mutes selected members", guild_ids=[SERVER_ID], default_member_permissions=8)
    async def mute(self, interaction: nextcord.Interaction, users: str = SlashOption(description="User or users to timeout"), reason: str = SlashOption(description="The reason for timeout")):
        print(f'{interaction.user} has used mute in {interaction.channel} at {curr_time()} UTC')
        print(f'{interaction.data}')
    
        await self.bot.wait_until_ready()
    
        m_list = await self._get_members_by_id(users)
        muted_list = database.get_data('muted', columns='user_id')
        id_count = {}

        for muted in muted_list:
            id = muted[0]
            if id in id_count:
                id_count[id] += 1
            else:
                id_count[id] = 1

        response_message = ''
        mute_channel_message = ''
        for member in m_list:
            count = id_count.get(str(member.id), 0)
            try:        
                if count == 0:
                    duration = '1 hour'
                    await member.edit(reason=reason, timeout=datetime.timedelta(minutes=60))
                    response_message += f'{member.mention} has been timed out for 1 hour. It is his first timeout.\n'
                elif count == 1:
                    duration = '1 day'
                    await member.edit(reason=reason, timeout=datetime.timedelta(minutes=1440))
                    response_message += f'{member.mention} has been timed out for 1 day. It is his second timeout.\n'
                elif count == 2:
                    duration = '1 week'
                    await member.edit(reason=reason, timeout=datetime.timedelta(minutes=10080))
                    response_message += f'{member.mention} has been timed out for 1 week. It is his third timeout.\n'
                elif count > 2:
                    duration = '1 week'
                    await member.edit(reason=reason, timeout=datetime.timedelta(minutes=10080))
                    response_message += f'{member.mention} has been timed out for 1 week. It is his {self.ordinal(count)} or higher timeout.\n'
                mute_channel_message += f'• Timed out {member.mention}\n     For {duration}.\n     Reason: {reason}\n     This is their {self.ordinal(count+1)} timeout.\n'

            except:
                response_message += f"Couldn't timeout {member.mention}. The user is administrator or has higher perms than the bot.\n"
                continue

            try:
                database.insert_data('muted', user_id=member.id, date=curr_time(), reason=reason, length=duration)
            except:
                response_message += f'There has been an error inserting {member.mention} into the database. Please contact the bot developer.\n'
            
        await interaction.response.send_message(response_message, ephemeral=True, delete_after=30)
        mute_channel = self.guild.get_channel(1106649636594266275)
        if mute_channel_message != None:
            await mute_channel.send(content=mute_channel_message)

            
                
