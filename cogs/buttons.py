import datetime
import os
import nextcord

from nextcord import Interaction, SlashOption
import pytz
from scrapper.id_scrapper import id_scrapper
from database import database
from nextcord.ext import commands, tasks
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
SERVER_ID = int(os.getenv('TESTSERVER_ID'))

CUSTOM_ID_PREFIX: str = 'request:'
valid_cities = ['bridgewatch', 'caerleon', 'fortsterling', 'lymhurst', 'martlock', 'thetford']
valid_stations = ['alchemy', 'butcher', 'cook', 'hunter', 'lumbermill', 'mage', 'mill', 'saddler', 'smelter', 'stonemason', 'tanner', 'toolmaker', 'warrior', 'weaver']
channels = {}


def curr_time():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")

class CloseView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @nextcord.ui.button(label="Finish", style=nextcord.ButtonStyle.green, custom_id="requestfinish")
    async def cancel(self, button: nextcord.ui.Button, interaction: Interaction):
        print(f"{interaction.user} has closed the thread {interaction.channel}")
        await interaction.channel.delete()
    
class RequestView(nextcord.ui.View):
    def __init__(self, stations_list, stations_coowners_list):
        super().__init__(timeout=None)
        self.stations_list = stations_list
        self.stations_coowners_list = stations_coowners_list
        self.city = None
        self.request_type = None
        self.name = None
        self.avaiable_stations = 0
        self.message = None

    @nextcord.ui.button(label="Cancel", style=nextcord.ButtonStyle.red, custom_id="requestcancel")
    async def cancel(self, button: nextcord.ui.Button, interaction: Interaction):
        print(f"{interaction.user} has closed the thread {interaction.channel}")
        await interaction.channel.delete()
        
    @nextcord.ui.button(label="Confirm", style=nextcord.ButtonStyle.blurple, custom_id="requestconfirm")
    async def finish(self, button: nextcord.ui.Button, interaction: Interaction):
        reactions = interaction.message.reactions

        self.message = await interaction.channel.history(limit=2, oldest_first=True).flatten()

        if len(reactions) == 0:
            reactions = self.message[1].reactions

        stations_to_add = []
        owners_list = []
        request_items_message = ""
        self.city = interaction.channel.parent.name[2:-12]

        if 'solo' in interaction.channel.name[-12:]:
            self.request_type = 'solo'
            self.name = interaction.channel.name[:len(interaction.channel.name)-12]
            
        if 'guild' in interaction.channel.name[-13:]:
            self.request_type = 'guild'
            self.name = interaction.channel.name[:len(interaction.channel.name)-13]
            
        if 'alliance' in interaction.channel.name[-16:]:
            self.request_type = 'alliance'
            self.name=interaction.channel.name[:len(interaction.channel.name)-16]

        # Count the available stations
        self.avaiable_stations = len([station for station in self.stations_list[self.city]])

        # loop through each reaction and get the station name if it has more than one reaction
        for reaction in reactions:
            if reaction.count > 1:
                stations_to_add.append(str(reaction)[2:-21])
                request_items_message += f"\n- {str(reaction)[2:-21].title()}"
 
        # loop through the selected stations and get their owners
        for request in stations_to_add:
            if request in self.stations_list[self.city]:
                for owner in self.stations_list[self.city][request]:
                    if owner not in owners_list:
                        owners_list.append(owner)
 
                        # add co-owners to the owners list
                        if self.city in self.stations_coowners_list and request in self.stations_coowners_list[self.city] and owner in self.stations_coowners_list[self.city][request]:
                            for coowner in self.stations_coowners_list[self.city][request][owner]:
                                if coowner not in owners_list:
                                    owners_list.append(coowner)
         
        # if no stations were selected, send a message indicating so
        if not stations_to_add:
            await interaction.response.send_message("```Please select stations you'd like to request by using emotes under the message above.```", ephemeral=True, delete_after=30)
 
        # if stations were selected, send a message to the owners list with the request
        else:
            owners_message = ' '.join([f"<@{owner}>" for owner in owners_list])
            final_message = f"**Requester:** <@{interaction.user.id}>\n**Owners:** {owners_message}\n**Request type:** {self.request_type}\n**Name:** {self.name}\n**Stations:** {request_items_message}"
            
            await interaction.channel.send(f"{final_message}")
 
            # handle solo requests
            if str(self.request_type) == 'solo' and len(stations_to_add) == self.avaiable_stations and len(stations_to_add) > 3:
                await interaction.channel.send(f"<@{interaction.user.id}> despite us asking to be mindful, you still requested all possible stations for a solo user. \nPlease provide explanation to why you would need access to all these stations.")
                 
            # handle guild requests
            if str(self.request_type) == 'guild':
                embed = nextcord.Embed(description=f"Please send screenshot of your guild looking like this:")
                embed.set_image("https://cdn.discordapp.com/attachments/841398443885068309/1079124508142731264/image.png")
                await interaction.channel.send(embed=embed)
            # handle alliance requests
            if str(self.request_type) == 'alliance':
                embed = nextcord.Embed(description=f"Please send screenshot of your alliance looking like this:")
                embed.set_image("https://cdn.discordapp.com/attachments/841398443885068309/1079124554254925844/image.png")
                await interaction.channel.send(embed=embed)
                 
            await self.message[1].delete()
            await interaction.channel.edit(auto_archive_duration=10080, name='? ' + interaction.channel.name)
            
    @nextcord.ui.button(label="Cancel", style=nextcord.ButtonStyle.red, custom_id="requestcancel")
    async def cancel(self, button: nextcord.ui.Button, interaction: Interaction):
        print(f"{interaction.user} has closed the thread {interaction.channel}")
        await interaction.channel.delete()
        
    async def interaction_check(self, interaction: Interaction):
        return True

class ButtonCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.parsed = False
        self.stations_coowners_list = {}
        self.stations_list = {}
        self.stations_images = {}
        self.emojis_array = []
        self.parse_values.start()
        self.bot.loop.create_task(self._create_autorequest_list())
        self.bot.loop.create_task(self._create_views())
        
    # Updates station owners list
    def _update_stations_list(self):
        for city, station_name, owner_id in database.get_data('stations', columns='DISTINCT city, station_name, owner_id'):
            self.stations_list.setdefault(city, {}).setdefault(station_name, []).append(owner_id)

    # Updates station co-owners list
    def _update_stations_coowners_list(self):
        for city, station_name, owner_id, coowner_id in database.get_data('stations_coowners', columns='DISTINCT city, station_name, owner_id, coowner_id'):
            self.stations_coowners_list.setdefault(city, {}).setdefault(station_name, {}).setdefault(owner_id, []).append(coowner_id)
    # Updates station image in database
    def _update_stations_images(self):
        self.stations_images = {city: image_link for city, image_link in database.get_data('images', columns='DISTINCT city, image_link')}

    # Updates emojis array
    async def _update_emojis(self):
        guild = self.bot.get_guild(SERVER_ID)
        self.emojis_array = await guild.fetch_emojis()
    
    # Creates list containing city : city.id for each autorequest channel
    async def _create_autorequest_list(self):
        await self.bot.wait_until_ready()
        guild = self.bot.get_guild(SERVER_ID)
        global channels
        for channel in guild.text_channels:
            if 'autorequest' in channel.name:
                channels[channel.name[2:channel.name.index("-")]] = channel.id

    # Creates persistent views
    async def _create_views(self):
        if getattr(self.bot, "request_view_set", False) is False:
            await self.bot.wait_until_ready()
            self.bot.request_view_set = True
            self.bot.add_view(RequestView(self.stations_list, self.stations_coowners_list))
            self.bot.add_view(CloseView())
            print(f"Persistent views found: {self.bot.persistent_views}")
    
    # Updates arrays and lists every 5 seconds. Used externally in Associates.py by changing parsed variable to False
    @tasks.loop(seconds=5)
    async def parse_values(self):
        if not self.parsed:
            await self.bot.wait_until_ready()
            await self._update_emojis()
            self._update_stations_coowners_list()
            self._update_stations_list()
            self._update_stations_images()
            self.parsed = True

    # Command for users to request a station
    @nextcord.slash_command(description="Request for associate", guild_ids=[SERVER_ID])
    async def request(
        self,
        interaction: nextcord.Interaction,
        type: str = SlashOption(description="Type of your request. Select accordingly.", choices={
            'Personal': 'solo',
            'Guild': 'guild',
            'Alliance': 'alliance'}
        ),
        name: str = SlashOption(
            description="Write full name of you character/guild/alliance accordingly to your previous choice."),
    ):
        print(f'{interaction.user} has used request in {interaction.channel} at {curr_time()} UTC')
        print(f'{interaction.data}')
        await interaction.response.defer(ephemeral=True, with_message=True)

        # Get city from interaction channel
        for chname, id in channels.items():
            if id == interaction.channel.id:
                city = chname

        # Check if command is being used in correct channel
        if interaction.channel.id not in channels.values():
            await interaction.followup.send(f"You shouldn't use that command here. Please use it in your city of choice: {' '.join([f'<#{channel}> ' for channel in channels.values()])}", ephemeral=True, delete_after=30)
            return
        
        name_check = id_scrapper(name)
        if type != 'alliance' and not name_check:
            if type == 'solo':
                await interaction.followup.send(f"Couldn't find user with name {name}. Are you sure you wrote your in-game name correctly?", ephemeral=True, delete_after=30)
            if type == 'guild':
                await interaction.followup.send(f"Couldn't find guild with name {name}. Are you sure you wrote your guild name correctly?", ephemeral=True, delete_after=30)
            return

        # Check if city has available stations
        if city not in self.stations_list:
            await interaction.followup.send(f"This city doesn't have any stations available. Please wait for updates.", ephemeral=True, delete_after=30)
            return

        # Check for existing threads by user
        for thread in interaction.channel.threads:
            if name in thread.name[:-8] and type in thread.name[len(name):-8] and (type == 'guild' or type == 'alliance'):
                await interaction.followup.send(f"*Looks like there is already thread for {type} {name} - <#{thread.id}>*", ephemeral=True, delete_after=15)
                await thread.send(f"Adding <@{interaction.user.id}> to the thread to avoid duplicates. If there is anything wrong please let us know")
                return
            if name in thread.name[:-8] and type in thread.name[len(name):-8]:
                await interaction.followup.send(f"*You already have an open thread - <#{thread.id}>*", ephemeral=True, delete_after=15)
                return

        # Create new thread and send confirmation message
        thread = await interaction.channel.create_thread(name=f"{name} {type} request", message=None, auto_archive_duration=10080, type=None)
        await interaction.followup.send(f"*Here is your request - <#{thread.id}>.\nUntil you submit your request the thread will be closed after 60 minutes of inactivity.*", ephemeral=True, delete_after=15)
        await thread.add_user(interaction.user)

        # Create the description for the embed
        description = f"**Available shops in {city.title()}**\n"
        avaiable_stations = 0
        for station in self.stations_list[city]:
            # Count the available stations
            avaiable_stations += 1

            # Add the emoji for the station
            for emoji in self.emojis_array:
                if str(emoji)[2:-21] == str(station):
                    description += f"\n**{emoji} {station.title()}**"

            # Add the owner and co-owners for the station
            for owner in self.stations_list[city][station]:
                description += f"\nOwner - <@{str(owner)}>"
                if city in self.stations_coowners_list and station in self.stations_coowners_list[city] and owner in self.stations_coowners_list[city][station]:
                    description += " Co-owners -" + \
                        ''.join(
                            [f" <@{str(coowner)}>" for coowner in self.stations_coowners_list[city][station][owner]])

        # Add additional information to the description
        description += "\nTo succesfully create a request, select stations using emojis below and pressing 'Confirm'\nTo cancel your request, press 'Cancel'. It will close the thread.\n**Use brain while requesting. All unreasonable requests will be ignored.**\n*If by any chance button are not responding, please contact <@158643072886898688> for help.*"

        # Create the embed and add the footer
        stations_embed = nextcord.Embed(
            title="Shop Information", description=description)
        if city in self.stations_images:
            stations_embed.set_image(self.stations_images[city.lower()])
        stations_embed.set_footer(
            text=f'Thread opened at {curr_time()} UTC\n',)

        # Create the request button and add it to the embed
        await thread.send(embed=stations_embed, view=RequestView(self.stations_list, self.stations_coowners_list))

        # Add the reactions for the available stations
        embed = await thread.history(limit=1).flatten()
        for emoji in self.emojis_array:
            if str(emoji)[2:-21] in self.stations_list[city]:
                try:
                    await embed[0].add_reaction(emoji)
                except:
                    print(
                        "Error adding reaction. Probably the embed has beed already deleted.")

    @nextcord.message_command(guild_ids=[SERVER_ID], default_member_permissions=8)
    async def close_one(self, interaction: nextcord.Interaction, message: nextcord.Message):
        thread = interaction.channel
        first_message = await thread.history(oldest_first=True, limit=1).flatten()

        if '✔ ' not in thread.name and '? ' in thread.name:
            await thread.edit(name='✔ ' + thread.name[2:])
            await thread.send(f"<@{first_message[0].mentions[0].id}> your request have been fulfilled.\nIf something's missing ping owners.\nIf everything is correct press the button below to close the thread.\nThread will automatically close after 24 hours.", view=CloseView())
        else:
            await interaction.response.send_message(f"This thread is already closed, or it didn't even open yet.", ephemeral=True, delete_after=30)
    
    @nextcord.message_command(guild_ids=[SERVER_ID], default_member_permissions=8)
    async def close_all(self, interaction: nextcord.Interaction, message: nextcord.Message):
        parent_channel = interaction.channel.parent
        counter = 0
        for thread in parent_channel.threads:
            if '✔ ' not in thread.name and '? ' in thread.name:
                counter += 1
                first_message = await thread.history(oldest_first=True, limit=1).flatten()
                await thread.edit(name='✔ ' + thread.name[2:])
                await thread.send(f"<@{first_message[0].mentions[0].id}> your request have been fulfilled.\nIf something's missing ping owners.\nIf everything is correct press the button below to close the thread.\nThread will automatically close after 24 hours.", view=CloseView())
        await interaction.response.send_message(f"Successfully closed {counter} threads.", ephemeral=True, delete_after=30)
    # Sends finish message to all threads older than given amount
    # @nextcord.slash_command(description="Sends close button and done message to all threads older than given amount in the channel.", guild_ids=[SERVER_ID], default_member_permissions=8)
    # async def set_done(
    #     self,
    #     interaction: nextcord.Interaction,
    #     age: int = SlashOption(description="Threads age in seconds.")):

    #     print(f'{interaction.user} has used set_done in {interaction.channel} at {curr_time()} UTC\n')

    #     counter = 0

    #     # Get the list of threads in the channel or its parent, depending on whether the channel is a private thread or not
    #     threads_list = interaction.channel.parent.threads if str(interaction.channel.type) == 'private_thread' else interaction.channel.threads

    #     # Loop through the threads and check if they are older than the given amount
    #     for thread in threads_list:
    #         diff = int(((datetime.datetime.utcnow().replace(tzinfo=pytz.utc)) -
    #                    (thread.created_at - datetime.timedelta(seconds=0))).total_seconds())
    #         if diff > amount and not thread.archived and '✔ ' not in thread.name and '? ' in thread.name:
    #             counter += 1
    #             # Set the thread's auto-archive duration to 24 hours
    #             await thread.edit(auto_archive_duration=10080, name='✔  ' + thread.name[2:])

    #             # Send a finish message to the thread's owner
    #             first_message = await thread.history(oldest_first=True, limit=1).flatten()
            
    #             await thread.send(f"<@{first_message[0].mentions[0].id}> your request have been fulfilled.\nIf something's missing ping owners.\nIf everything is correct press the button below to close the thread.\nThread will automatically close after 24 hours.", view=CloseView())

    #     # Send a response message indicating the number of threads that were finished, or that none were found
    #     if counter != 0:
    #         await interaction.response.send_message(f"Sent finished message to {counter} threads older than {amount} seconds.", ephemeral=True, delete_after=5)
    #     else:
    #         await interaction.response.send_message(f"Didn't find any unfinished threads older than {amount} seconds.", ephemeral=True, delete_after=5)
