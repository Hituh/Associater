import os
import nextcord
import discord
import datetime
import threading

from typing import Optional
from nextcord import Interaction, SlashOption, Colour
from nextcord.ext import commands
from scrapper.id_scrapper import id_scrapper
import pytz

from aux_libraries import database

from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = nextcord.Intents.all()
intents.members = True
bot = commands.Bot(intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f'        {bot.user} has connected to Discord!\n        Currently it is connected to the following servers:')
    for guild in bot.guilds:
        print('       ',guild)
    
valid_cities = ['bridgewatch', 'caerleon', 'sterling', 'lymhurst', 'martlock', 'thetford']
valid_stations = ['alchemy', 'butcher', 'cook', 'hunter', 'lumbermill', 'mage', 'mill', 'saddler', 'smelter', 'stonemason', 'tanner', 'toolmaker', 'warrior', 'weaver']
stations_images = {}
stations_list = {}
stations_coowners_list = {}
request_channels = ['1076824842155860059', '1076824842155860060', '1076824842155860061', '1076824842155860062', '1076824842155860063', '1076824842155860064']


class ButtonRequest(nextcord.ui.View):
    def __init__(self, request_type, city, name, avaiable_stations):
        super().__init__(timeout=None)
        self.value = None
        self.message = None 
        self.city = city
        self.request_type = request_type
        self.name = name
        self.avaiable_stations = avaiable_stations
         
    @nextcord.ui.button(label="Confirm", style=nextcord.ButtonStyle.green)
    async def finish(self, button: nextcord.ui.Button, interaction: Interaction):
        reactions = interaction.message.reactions
        stations_to_add = []
        owners_list = []
        request_items_message = ""

        # loop through each reaction and get the station name if it has more than one reaction
        for reaction in reactions:
            if reaction.count > 1:
                stations_to_add.append(str(reaction)[2:-21])
                request_items_message += f"\n{str(reaction)[2:-21].title()}"

        # loop through the selected stations and get their owners
        for request in stations_to_add:
            if request in stations_list[self.city]:
                for owner in stations_list[self.city][request]:
                    if owner not in owners_list:
                        owners_list.append(owner)

                        # add co-owners to the owners list
                        if self.city in stations_coowners_list and request in stations_coowners_list[self.city] and owner in stations_coowners_list[self.city][request]:
                            for coowner in stations_coowners_list[self.city][request][owner]:
                                if coowner not in owners_list:
                                    owners_list.append(coowner)

        # if no stations were selected, send a message indicating so
        if not stations_to_add:
            await interaction.response.send_message("```If it wasn't obvious you need to choose at least one station you'd like to request.```", ephemeral=True, delete_after=30)

        # if stations were selected, send a message to the owners list with the request
        else:
            owners_message = ' '.join([f"<@{owner}>" for owner in owners_list])
            await interaction.channel.send(f"{owners_message} here is <@{interaction.user.id}> **{self.request_type}** request for **{self.name}**")

            embed = discord.Embed(title="Stations list", description=f"{request_items_message}")
            await interaction.channel.send(embed=embed)
            # handle solo requests
            if str(self.request_type) == 'solo' and len(stations_to_add) == self.avaiable_stations and len(stations_to_add) > 3:
                await interaction.channel.send(f"<@{interaction.user.id}> despite us asking to be mindful, you still requested all possible stations for a solo user. \nPlease provide explanation to why you would need access to all these stations.")
                
            # handle guild requests
            if str(self.request_type) == 'guild':
                embed = discord.Embed(description=f"<@{interaction.user.id}> please send screenshot of your guild looking like this:")
                embed.set_image("https://cdn.discordapp.com/attachments/841398443885068309/1079124508142731264/image.png")
                await interaction.channel.send(embed=embed)
            # handle alliance requests
            if str(self.request_type) == 'alliance':
                embed = discord.Embed(description=f"<@{interaction.user.id}> please send screenshot of your alliance looking like this:")
                embed.set_image("https://cdn.discordapp.com/attachments/841398443885068309/1079124554254925844/image.png")
                await interaction.channel.send(embed=embed)
                
            await self.message.delete()
    @nextcord.ui.button(label="Cancel", style=nextcord.ButtonStyle.red)
    async def cancel(self, button: nextcord.ui.Button, interaction: Interaction):
        print(f"{interaction.user} has closed the thread {interaction.channel}")
        await interaction.channel.delete()

        
class ButtonFinish(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.message = None
    
    @nextcord.ui.button(label="Finish", style=nextcord.ButtonStyle.green)
    async def finish(self, button: nextcord.ui.Button, interaction: Interaction):
        try:
            await self.message.delete()
            await interaction.channel.send(f"```Request closed by {interaction.user}```")
            await interaction.channel.edit(archived=True)
        except:
            print("Button has been already used")


def _delete_archived_threads():
    # This function runs periodically every 1 second
    threading.Timer(1, _delete_archived_threads).start()

    now = datetime.datetime.now()

    current_time = now.strftime("%H:%M:%S")
    print("Current Time =", current_time)

    if(current_time == '02:11:00'):  # check if matches with the desired time
        print('sending message')
    for thread in threading.enumerate(): 
        print(thread.name)

#Returns city string based on interaction.channel.id
def _get_city_by_id(channel_id):
    if(str(channel_id) == "1076824842155860059"): return 'lymhurst'
    if(str(channel_id) == "1076824842155860060"): return 'bridgewatch'
    if(str(channel_id) == "1076824842155860061"): return 'martlock'
    if(str(channel_id) == "1076824842155860062"): return 'thetford'
    if(str(channel_id) == "1076824842155860063"): return 'sterling'
    if(str(channel_id) == "1076824842155860064"): return 'caerleon'

#Returns embed colour based on city name   
def _set_embed_colour(city):
    if city == 'sterling':
        return (0xFFFFFF)
    if city == 'lymhurst':
        return (Colour.green())
    if city == 'bridgewatch':
        return (Colour.orange())
    if city == 'martlock':
        return (Colour.blue())
    if city == 'thetford':
        return (Colour.purple())
    if city == 'caerleon':
        return (Colour.red())

#Updates in-code station owners array
def _update_stations_list():
    global stations_list
    stations_list = {}
    stations = database.get_data('stations', columns='DISTINCT city, station_name, owner_id')

    for station in stations:
        city = station[0]
        station_name = station[1]
        owner_id = station[2]
        
        if city not in stations_list.keys():
            stations_list[city] = {}
        if station_name not in stations_list[city].keys():
            stations_list[city][station_name] = []
        stations_list[city][station_name].append(owner_id)
    
#Updates in-code station co-owners array
def _update_stations_coowners_list():
    global stations_coowners_list
    stations_coowners_list = {}
    stations_coowners = database.get_data('stations_coowners', columns='DISTINCT city, station_name, owner_id, coowner_id')
    for station in stations_coowners:
        city = station[0]
        station_name = station[1]
        owner_id = station[2]
        coowner_id = station[3]
        if city not in stations_coowners_list.keys():
            stations_coowners_list[city] = {}
        if station_name not in stations_coowners_list[city].keys():
            stations_coowners_list[city][station_name] = {}
        if owner_id not in stations_coowners_list[city][station_name].keys():
             stations_coowners_list[city][station_name][owner_id] = []
        stations_coowners_list[city][station_name][owner_id].append(coowner_id) 
  
#Updates station image in database      
def _update_stations_images():
    global stations_images
    stations_images = {}
    images = database.get_data('images', columns='DISTINCT city, image_link')
    for image in images:
        city = image[0]
        image_link = image[1]
        stations_images[city] = image_link
  
#Returns user id. Takes user class or user name as input.
def _get_user_id(value):
    guild = bot.get_guild(int(os.getenv('TESTSERVER_ID')))
    if(value[0] == '<'):
        user_id = guild.get_member(int(value[2:-1])).id
    else:
        for member in guild.members:
            if member.name.lower() == value.lower():
                user_id = member.id
    return user_id
              
#Displays embed of current stations in chosen city
@bot.slash_command(description='Shows information about stations in specified city.', guild_ids=[int(os.getenv('TESTSERVER_ID'))], default_member_permissions=8)
async def display_stations(
    interaction: nextcord.Interaction, 
    city: str = SlashOption(name='city', description='Choose city to display.', choices={
        'Sterling': 'sterling',
        'Lymhurst': 'lymhurst',
        'Bridgewatch': 'bridgewatch',
        'Martlock': 'martlock',
        'Thetford': 'thetford',
        'Caerleon': 'caerleon'
    })):
    channel = interaction.channel
    print(f'{interaction.user} has used display_stations in {interaction.channel} at {datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")} UTC\nInteraction message : {interaction.data}')
    
    #Check if image exists in database
    if city in stations_images and city in stations_list.keys(): 
        image = stations_images[city.lower()]
        description = (f'**Avaiable shops in {city.title()}**')
        await interaction.response.send_message(f"*You have selected {city} to display, the full message will be shown shortly*", ephemeral=True, delete_after=15)         
        
        #Creates owners and co-owners string to display in embed
        for station, owners in stations_list[city].items():
            description += f'\n**{station.title()}**'
            for owner in owners:
                description += f'\nOwner - <@{owner}>'
                if city in stations_coowners_list.get(station, {}) and owner in stations_coowners_list[station][city]:
                    description += ' Co-owners -'
                    description += ''.join(f' <@{coowner}>' for coowner in stations_coowners_list[city][station][owner])
 
        #Embed creation          
        embedColor = _set_embed_colour(city)
        em = nextcord.Embed(
                description=description,
                color=embedColor)
        em.set_author(name=f'Please use /request for requesting\n')
        em.set_image(image)
        em.set_footer(text=f'Updated at {datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")} UTC\n',)
        await channel.send(embed=em)
        
    #Displays empty city embed
    elif city not in stations_list:
        embedColor = _set_embed_colour(city)
        description = f"We currently don't own any shops in {city.title()}, please wait for the next cycle."
        em = nextcord.Embed(
                description=description,
                color=embedColor)
        em.set_image('https://thumbs.dreamstime.com/b/please-wait-test-clock-middle-delay-48693489.jpg')
        em.set_footer(text=f'Updated at {datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")} UTC\n',)
        await channel.send(embed=em)    
        await interaction.response.send_message(f"{city} doesn't have any shops set. If that isn't intended please set shops for the city and try again. If problem keeps appearing please contact Hituh", ephemeral=True, delete_after=5)         

#Displays all stations owner by provided owner
@bot.slash_command(description='Displays all stations from a specific owner.', guild_ids=[int(os.getenv('TESTSERVER_ID'))], default_member_permissions=8)
async def owner_stations(
    interaction: nextcord.Interaction, 
    owner: Optional[str] = SlashOption(description="Ping or the owner server name, if empty will display your stations")):
    print(f'{interaction.user} has used owner_stations in {interaction.channel} at {datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")} UTC\nInteraction message : {interaction.data}')
  
    owner_id = _get_user_id(owner or interaction.user.name)
    stations = []
    for city in stations_list.keys():
        owner_stations = [f'{city} -> {station}\n' for station in stations_list[city] for owner in stations_list[city][station] if str(owner) == str(owner_id)]
        if owner_stations:
            stations.append(f'**{city.title()}**\n```{"".join(owner_stations)}```\n')
    if stations:
        owner_header = f'Stations list for <@{owner_id}>\n'
        await interaction.response.send_message(owner_header + "".join(stations), ephemeral=True, delete_after=30)
    else:
        await interaction.response.send_message(f"No stations found for <@{owner_id}> in any city.", ephemeral=True, delete_after=30)

#Add station to provided owner. If not owner provided defaults to interaction.user
@bot.slash_command(description='Adds a station to the list of stations.', guild_ids=[int(os.getenv('TESTSERVER_ID'))], default_member_permissions=8)
async def add_station(
    interaction: nextcord.Interaction, 
    city: str = SlashOption(name='city', description='Chosen city', choices={
       'Sterling': 'sterling',
       'Lymhurst': 'lymhurst',
       'Bridgewatch': 'bridgewatch',
       'Martlock': 'martlock',
       'Thetford': 'thetford',
       'Caerleon': 'caerleon'
    }),
    station: str = SlashOption(name='station', description='Chosen station', choices={
        "Alchemist's Lab" : 'alchemy',
        "Butcher" : 'butcher', 
        "Cook" : 'cook', 
        "Hunter's Lodge" : 'hunter', 
        "Lumbermill" : 'lumbermill', 
        "Mage's Tower" : 'mage', 
        "Mill" : 'mill', 
        "Saddler" : 'saddler', 
        "Smelter" : 'smelter', 
        "Stonemason" : 'stonemason', 
        "Tanner" : 'tanner', 
        "Toolmaker" : 'toolmaker', 
        "Warrior's Forge" : 'warrior', 
        "Weaver" : 'weaver'
    }), 
    owner: Optional[str] = SlashOption(description="Ping the owner, if empty will add to your stations")):
    print(f'{interaction.user} has used add_station in {interaction.channel} at {datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")} UTC\nInteraction message : {interaction.data}')
    
    owner_id = _get_user_id(owner) if owner else _get_user_id(interaction.user.name)
    city_title = city.title()
    station_title = station.title()
    
    if (city, station, owner_id) not in database.get_data('stations', columns='DISTINCT city, station_name, owner_id'):
        database.insert_data('stations', city=city, station_name=station, owner_id=owner_id)
        _update_stations_list()
        await interaction.response.send_message(f"{station_title} added for <@{owner_id}> at {city_title}", ephemeral=True, delete_after=30)
    else:
        await interaction.response.send_message(f'{station_title} is already added for <@{owner_id}> at {city_title}.', ephemeral=True, delete_after=30).user

#Adds co-owner to all stations of selected owner
@bot.slash_command(description='Adds co-owners to your stations.', guild_ids=[int(os.getenv('TESTSERVER_ID'))], default_member_permissions=8)
async def add_coowner(
    interaction: nextcord.Interaction, 
    coowner: str = SlashOption(name='coowner', description='Ping your desired co-owner')):
    print(f'{interaction.user} has used add_coowner in {interaction.channel} at {datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")} UTC\nInteraction message : {interaction.data}')
    
    coowner_id = _get_user_id(coowner)
    guild = bot.get_guild(int(os.getenv('TESTSERVER_ID')))
    member = guild.get_member(int(coowner_id))
    if not member:
        await interaction.response.send_message(f"I couldn't find <@{coowner_id}> in the server. If this not intentional, please contant <@158643072886898688>", ephemeral=True, delete_after=30)
    #Ultra complicated command that checks for too many things. Pray it doesn't break
    else: 
        coowner_id = _get_user_id(coowner)     
        coowners_temp = database.get_data('stations_coowners', columns='DISTINCT city, station_name, owner_id, coowner_id')
        counter_all = 0
        counter_added = 0
        for city in stations_list:
            for station in stations_list[city]:
                for owner in stations_list[city][station]:
                    if owner == interaction.user.id:
                        counter_all += 1
                        if (city, station, owner, coowner_id) in coowners_temp:
                            counter_added += 1
                        else:
                            database.insert_data('stations_coowners', city=city, station_name=station, owner_id=interaction.user.id, coowner_id=coowner_id)
        if counter_all == counter_added:
            await interaction.response.send_message(f"<@{coowner_id}> is already co-owner of all your stations.", ephemeral=True, delete_after=30)
        elif counter_added == 0:
            await interaction.response.send_message(f"<@{coowner_id}> has been added as coowner of all your stations.", ephemeral=True, delete_after=30)
        elif counter_all != counter_added:
            await interaction.response.send_message(f"<@{coowner_id}> has been added as coowner of all the missing stations.", ephemeral=True, delete_after=30)
        _update_stations_coowners_list() 
 
#Removes given co-owner from interaction.user's stations
@bot.slash_command(description='Adds co-owners to your stations.', guild_ids=[int(os.getenv('TESTSERVER_ID'))], default_member_permissions=8)
async def remove_coowner(
    interaction: nextcord.Interaction, 
    coowner: str = SlashOption(name='coowner', description='Ping your desired co-owner')):
    print(f'{interaction.user} has used remove_coowner in {interaction.channel} at {datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")} UTC\nInteraction message : {interaction.data}')
    coowner_id = _get_user_id(coowner)
    try:
        database.delete_data('stations_coowners', where=f'WHERE owner_id = {interaction.user.id} and coowner_id = {coowner_id}') 
        _update_stations_coowners_list() 
        await interaction.response.send_message(f"<@{coowner_id}> has been removed as coowner of your stations.", ephemeral=True, delete_after=30)
    except:
        await interaction.response.send_message(f"Something went wrong. Please check if you wrote the command correctly and try again. If problem keeps occuring please contact <@158643072886898688>", ephemeral=True, delete_after=30)
 
#Deletes chosen station in city from selected owner. Defaults to interaction.user       
@bot.slash_command(description='Delete as station from owner', guild_ids=[int(os.getenv('TESTSERVER_ID'))], default_member_permissions=8)
async def delete_station(
    interaction: nextcord.Interaction,
    city: str = SlashOption(name='city', description='Chosen city', choices={
       'Sterling': 'sterling',
       'Lymhurst': 'lymhurst',
       'Bridgewatch': 'bridgewatch',
       'Martlock': 'martlock',
       'Thetford': 'thetford',
       'Caerleon': 'caerleon'
    }),
    station: str = SlashOption(name='station', description='Chosen station', choices={
        "Alchemist's Lab" : 'alchemy',
        "Butcher" : 'butcher', 
        "Cook" : 'cook', 
        "Hunter's Lodge" : 'hunter', 
        "Lumbermill" : 'lumbermill', 
        "Mage's Tower" : 'mage', 
        "Mill" : 'mill', 
        "Saddler" : 'saddler', 
        "Smelter" : 'smelter', 
        "Stonemason" : 'stonemason', 
        "Tanner" : 'tanner', 
        "Toolmaker" : 'toolmaker', 
        "Warrior's Forge" : 'warrior', 
        "Weaver" : 'weaver'
    }), 
    owner: Optional[str] = SlashOption(description="Ping the owner, if empty will remove your station")): 
    print(f'{interaction.user} has used delete_station in {interaction.channel} at {datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")} UTC\nInteraction message : {interaction.data}')
 
    owner_id = _get_user_id(interaction.user.name) if owner is None else _get_user_id(owner)
        
    if (str(city), str(station), int(owner_id)) in database.get_data('stations', columns='DISTINCT city, station_name, owner_id'):
        database.delete_data('stations', where=f'WHERE city = "{city}" AND station_name = "{station}" and owner_id = {owner_id}')
        database.delete_data('stations_coowners', where=f'WHERE city = "{city}" AND station_name = "{station}" and owner_id = {owner_id}')

        _update_stations_list()
        await interaction.response.send_message(f"{station.title()} removed from <@{owner_id}> at {city.title()}", ephemeral=True, delete_after=30)         
    else:
        await interaction.response.send_message(f'{station.title()} owned by <@{owner_id}> in {city.title()} not found in database.', ephemeral=True, delete_after=30)
      
#Sets stations image to given city. Needs URL to IMAGE to display properly.
@bot.slash_command(description='Sets the image of specified city', guild_ids=[int(os.getenv('TESTSERVER_ID'))], default_member_permissions=8)
async def set_image(
    interaction: nextcord.Interaction, 
    city: str = SlashOption(name='city', description='Chosen city', choices={
       'Sterling': 'sterling',
       'Lymhurst': 'lymhurst',
       'Bridgewatch': 'bridgewatch',
       'Martlock': 'martlock',
       'Thetford': 'thetford',
       'Caerleon': 'caerleon'
    }),
    image: str = SlashOption(description="Image to display. Needs to be URL to an IMAGE.")): 
    print(f'{interaction.user} has used set_image in {interaction.channel} at {datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")} UTC\nInteraction message : {interaction.data}')
    if city.lower() in stations_images.keys():
        database.delete_data('images', where=f'WHERE city = "{city.lower()}"')
    
    database.insert_data('images', city=city.lower(), image_link = image)
    _update_stations_images() 
    await interaction.response.send_message(f"Image for {city} updated succesfully", ephemeral=True, delete_after=30)         

#Command for users to request a station
@bot.slash_command(description="Request for associate", guild_ids=[int(os.getenv('TESTSERVER_ID'))])
async def request(
        interaction: nextcord.Interaction, 
        type: str = SlashOption(description="Type of your request. Select accordingly.", choices={
            'Personal': 'solo',
            'Guild': 'guild',
            'Alliance': 'alliance'} 
        ),
        name: str = SlashOption(description="Write full name of you character/guild/alliance accordingly to your previous choice."),
       ):
    print(f'{interaction.user} has used request in {interaction.channel} at {datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")} UTC\nInteraction message : {interaction.data}')
    channel = interaction.channel.id
    city = _get_city_by_id(channel)

    # Get city from interaction channel
    city = _get_city_by_id(interaction.channel.id)

    # Check if command is being used in correct channel
    if str(interaction.channel.id) not in request_channels:
        await interaction.response.send_message(f"You shouldn't use that command here. Please use it in your city of choice: {' '.join([f'<#{channel}> ' for channel in request_channels])}", ephemeral=True, delete_after=30)
        return
    name_check = id_scrapper(name)
    print(name_check)
    if type != 'alliance' and not name_check:
        if type == 'solo':
            await interaction.response.send_message(f"Couldn't find user with name {name}. Are you sure you wrote your in-game name correctly?", ephemeral=True, delete_after=30)
        if type == 'guild':
            await interaction.response.send_message(f"Couldn't find guild with name {name}. Are you sure you wrote your guild name correctly?", ephemeral=True, delete_after=30)
        return
    
    # Check if city has available stations
    if city not in stations_list:
        await interaction.response.send_message(f"This city doesn't have any stations available. Please wait for updates.", ephemeral=True, delete_after=30)
        return

    # Check for existing threads by user
    for thread in interaction.channel.threads:
        if name in thread.name[:-8] and type in thread.name[len(name):-8] and type == 'guild' or type == 'alliance':
            await interaction.response.send_message(f"*Looks like there is already thread for {type} {name} - <#{thread.id}>*", ephemeral=True, delete_after=15)
            await thread.send(f"Adding <@{interaction.user.id}> to the thread to avoid duplicates. If there is anything wrong please let us know")
            return
        if name in thread.name[:-8] and type in thread.name[len(name):-8]:
            await interaction.response.send_message(f"*You already have an open thread - <#{thread.id}>*", ephemeral=True, delete_after=15)
            return
  
        
    # Create new thread and send confirmation message
    thread = await interaction.channel.create_thread(name=f"{name} {type} request", message=None, auto_archive_duration=60, type=None)
    await interaction.response.send_message(f"*Here is your request - <#{thread.id}>.\nUntil you submit your request the thread will be closed after 60 minutes of inactivity.*", ephemeral=True, delete_after=15)
    await thread.add_user(interaction.user)

    # Create and send shop information embed
    guild = bot.get_guild(int(os.getenv('TESTSERVER_ID')))
    emojis = await guild.fetch_emojis()

    # Create the description for the embed
    description = f"**Available shops in {city.title()}**\n"
    avaiable_stations = 0
    for station in stations_list[city]:
        # Count the available stations
        avaiable_stations += 1

        # Add the emoji for the station
        for emoji in emojis:
            if str(emoji)[2:-21] == str(station):
                description += f"\n**{emoji} {station.title()}**"

        # Add the owner and co-owners for the station
        for owner in stations_list[city][station]:
            description += f"\nOwner - <@{str(owner)}>"
            if city in stations_coowners_list and station in stations_coowners_list[city] and owner in stations_coowners_list[city][station]:
                description += " Co-owners -" + ''.join([f" <@{str(coowner)}>" for coowner in stations_coowners_list[city][station][owner]])

    # Add additional information to the description
    description += "\nTo succesfully create a request, select stations using emojis below and pressing 'Confirm'\nTo cancel your request, press 'Cancel'. It will close the thread.\n**Use brain while requesting. All unreasonable requests will be ignored.**\n*If by any chance button are not responding, please contact <@158643072886898688> for help.*"

    # Create the embed and add the footer
    stations_embed = discord.Embed(title="Shop Information", description=description)
    if city in stations_images:
        stations_embed.set_image(stations_images[city.lower()])
    stations_embed.set_footer(text=f'Thread opened at {datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")} UTC\n',)

    # Create the request button and add it to the embed
    button_request = ButtonRequest(request_type=type, city=city, name=name, avaiable_stations=avaiable_stations)
    await thread.send(embed=stations_embed, view=button_request)

    # Add the reactions for the available stations
    embed = await thread.history(limit=1).flatten()
    button_request.message = embed[0]
    for emoji in emojis:
        if str(emoji)[2:-21] in stations_list[city]:
            await embed[0].add_reaction(emoji)
    
#Mass delete messages
@bot.slash_command(description="Deletes given amount of messages from current channel.", guild_ids=[int(os.getenv('TESTSERVER_ID'))], default_member_permissions=8)  
async def delete_messages(
    interaction: nextcord.Interaction, 
    amount: int = SlashOption(description="Amount of messages to delete")):
    print(f'{interaction.user} has used delete_messages in {interaction.channel} at {datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")} UTC\nInteraction message : {interaction.data}')
    if amount > 100:
        await interaction.response.send_message(f"Amount needs to be less than 100", ephemeral=True, delete_after=5) 
    else:
        await interaction.channel.purge(limit = amount)
        await interaction.response.send_message(f"Done deleting {amount} messages", ephemeral=True, delete_after=5)    
               
# Sends finish message to all threads older than given amount
@bot.slash_command(description="Sends close button and done message to all threads older than given amount in the channel.", guild_ids=[int(os.getenv('TESTSERVER_ID'))], default_member_permissions=8)
async def set_done(
    interaction: nextcord.Interaction,
    amount: int = SlashOption(description="Threads age in seconds.")): 

    print(f'{interaction.user} has used set_done in {interaction.channel} at {datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")} UTC\nInteraction message : {interaction.data}')

    counter = 0

    # Get the list of threads in the channel or its parent, depending on whether the channel is a private thread or not
    threads_list = interaction.channel.parent.threads if str(interaction.channel.type) == 'private_thread' else interaction.channel.threads

    
    # Loop through the threads and check if they are older than the given amount
    for thread in threads_list:
        diff = int(((datetime.datetime.utcnow().replace(tzinfo=pytz.utc)) - (thread.created_at - datetime.timedelta(seconds=0))).total_seconds())
        if diff > amount and not thread.archived:
            # Set the thread's auto-archive duration to 24 hours
            await thread.edit(auto_archive_duration=1440)

            # Send a finish message to the thread's owner
            first_message = await thread.history(oldest_first = True, limit=1).flatten()
            button = ButtonFinish()      
            await thread.send(f"<@{first_message[0].mentions[0].id}> your request have been fulfilled. Press the button below to close the thread or the owners that there's something missing.\nThread will automatically close after 24 hours.", view=button)
            
            # Set the button's message ID to the ID of the message that was just sent
            button_id = await thread.history(limit=1).flatten()
            button.message = button_id[0]
            counter += 1             

    # Send a response message indicating the number of threads that were finished, or that none were found
    if counter != 0:
        await interaction.response.send_message(f"Sent finished message to {counter} threads older than {amount} seconds.", ephemeral=True, delete_after=5)
    else:
        await interaction.response.send_message(f"Didn't find any threads older than {amount} seconds.", ephemeral=True, delete_after=5)

@bot.slash_command(description="Command for testing.", guild_ids=[int(os.getenv('TESTSERVER_ID'))], default_member_permissions=8)
async def test_command(interaction: nextcord.Interaction):
    await interaction.response.send_message(f"Tested", ephemeral=True, delete_after=10)


if __name__ == '__main__':

    database.connect('stations.db')
    database.create_table('stations_coowners', [('city', 'TEXT'), ('station_name', 'TEXT'), ('owner_id', 'INTEGER'), ('coowner_id', 'INTEGER')])
    database.create_table('stations', [('city', 'TEXT'), ('station_name', 'TEXT'), ('owner_id', 'INTEGER')])
    database.create_table('images', [('city', 'TEXT UNIQUE'), ('image_link', 'TEXT')])
    
    
    _update_stations_list()
    _update_stations_images()
    _update_stations_coowners_list()
       
    bot.run(os.getenv('BOT_TOKEN'))
    

    
    
