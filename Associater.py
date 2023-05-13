import os
import nextcord
import datetime
import pytz
import logging

from typing import Optional
from nextcord import Interaction, SlashOption, Colour
from nextcord.ext import commands
from cogs.bgtasks import TaskCog
from cogs.buttons import ButtonCog
from cogs.muted import MutedCog
from database import database
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
SERVER_ID = int(os.getenv('TESTSERVER_ID'))
TOKEN = os.getenv('BOT_TOKEN')

logger = logging.getLogger('nextcord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(
    filename='nextcord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

intents = nextcord.Intents(members = True, emojis = True, reactions = True, guilds = True, messages = True, message_content = True)
bot = commands.Bot(intents=intents)

@bot.event
async def on_ready():
    await _prepare_variables()
    global emojis
    guild = bot.get_guild(SERVER_ID)
    emojis = await guild.fetch_emojis()
    
    print(f'        {bot.user} has connected to Discord!\n        Currently it is connected to the following servers:')
    for guild in bot.guilds:
        print('       ',guild)
    
    
valid_cities = ['bridgewatch', 'caerleon', 'fortsterling', 'lymhurst', 'martlock', 'thetford']
valid_stations = ['alchemy', 'butcher', 'cook', 'hunter', 'lumbermill', 'mage', 'mill', 'saddler', 'smelter', 'stonemason', 'tanner', 'toolmaker', 'warrior', 'weaver']
stations_images = {}
stations = {}
stations_coowners = {}
emojis = []
request_channels = []

# Finding all autorequest channels in guild. Channels need to have 'autorequest' in their name
def _get_autorequest_channels():
    global request_channels
    guild = bot.get_guild(SERVER_ID)
    channels_found = False
    for channel in guild.text_channels:
        if 'autorequest' in channel.name:
            if channels_found:
                print(channel.name)
                request_channels.append(channel.id)
            else:
                print('Autorequest channels found:')
                print(channel.name)
                request_channels.append(channel.id)
                channels_found = True
          
# Returns embed colour based on city name   
def _set_embed_colour(city):
    colors = {'fortsterling': 0xFFFFFF, 'lymhurst': Colour.green(), 'bridgewatch': Colour.orange(), 'martlock': Colour.blue(), 'thetford': Colour.purple(), 'caerleon': Colour.red()}
    return colors.get(city)

#Updates in-code station owners array
def _update_stations_list():
    global stations
    stations = {}
    for city, station_name, owner_id in database.get_data('stations', columns='DISTINCT city, station_name, owner_id'):
        stations.setdefault(city, {}).setdefault(station_name, []).append(owner_id)
    buttonCog.parsed = False
    
# Updates in-code station co-owners array
def _update_stations_coowners():
    global stations_coowners
    stations_coowners = {}
    for owner_id, coowner_id in database.get_data('stations_coowners', columns='DISTINCT owner_id, coowner_id'):
        stations_coowners.setdefault(owner_id, []).append(coowner_id)
    buttonCog.parsed = False
    
def curr_time():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")

# Updates station image in database      
def _update_stations_images():
    global stations_images
    stations_images = {}
    for city, image_link in database.get_data('images', columns='DISTINCT city, image_link'):
        stations_images.setdefault(city, []).append(image_link)
    buttonCog.parsed = False

# Initializing function, calling all functions to prepare variables for the bot
async def _prepare_variables():
    await bot.wait_until_ready()
    _update_stations_list()
    _update_stations_coowners()
    _update_stations_images()  
    _get_autorequest_channels()

#Returns user id. Takes user class or user name as input.
def _get_user_id(value):
    user_id = None
    if len(value[2:-1]) == 18 and value[2:-1].isdigit():
        user_id = value[2:-1]
    if (user_id == None):
        guild = bot.get_guild(SERVER_ID)
        for member in guild.members:
            if (member.nick is not None and member.nick == value) or member.name == value:
                user_id = member.id
    
    return user_id
   
# Displays embed of current stations in chosen city
@bot.slash_command(description='Shows information about stations in selected city.', guild_ids=[SERVER_ID], default_member_permissions=8)
async def display_stations(
    interaction: nextcord.Interaction, 
    city: str = SlashOption(name='city', description='Choose city to display.', choices={
        'Fort Sterling': 'fortsterling',
        'Lymhurst': 'lymhurst',
        'Bridgewatch': 'bridgewatch',
        'Martlock': 'martlock',
        'Thetford': 'thetford',
        'Caerleon': 'caerleon'
    })):
    channel = interaction.channel
    print(f'{interaction.user} has used display_stations in {interaction.channel} at {curr_time()} UTC')
    
    #Check if image exists in database
    if city in stations_images and city in stations.keys(): 
        image = stations_images[city][0]
        description = (f'**Avaiable shops in {city.title()}**')
        await interaction.response.send_message(f"*You have selected {city} to display, the full message will be shown shortly*", ephemeral=True, delete_after=10)         
        
        #Creates owners and co-owners string to display in embed
        for station, owners in stations[city].items():
            description += f'\n**{station.title()}**'
            for owner in owners:
                description += f'\nOwner - <@{owner}>'
                if owner in stations_coowners:
                    description +=  f' Co-owners - '
                    for coowner in stations_coowners[owner]:
                        description += f'<@{coowner}> '
 
        #Embed creation   
        description += f'\n\nPlease use /request for requesting\n*Updated at {curr_time()} UTC*\n'
        await channel.send(description)
        await channel.send(image)
        
    #Displays empty city embed
    elif city not in stations:
        embedColor = _set_embed_colour(city)
        description = f"We currently don't own any shops in {city.title()}, please wait for the next cycle."
        em = nextcord.Embed(
                description=description,
                color=embedColor)
        em.set_image('https://thumbs.dreamstime.com/b/please-wait-test-clock-middle-delay-48693489.jpg')
        em.set_footer(text=f'Updated at {curr_time()} UTC\n',)
        await channel.send(embed=em)    
        await interaction.response.send_message(f"{city} doesn't have any shops set. If that isn't intended please set shops for the city and try again. If problem keeps appearing please contact <@158643072886898688>", ephemeral=True, delete_after=5)

# Displays all stations owned by provided owner
@bot.slash_command(description='Displays all stations from given owner.', guild_ids=[SERVER_ID], default_member_permissions=8)
async def owner_stations(
    interaction: nextcord.Interaction, 
    owner: Optional[str] = SlashOption(description="Ping the owner or write his server name, if empty will display your stations")):
    print(f'{interaction.user} has used owner_stations in {interaction.channel} at {curr_time()} UTC\n')
  
    owner_id = _get_user_id(owner or interaction.user.name)
    description = ''
    for city in stations:
        for station in stations[city]:
            for owner in stations[city][station]:
                if str(owner_id) == str(owner):
                    if description == '':
                        description = f'**Displaying stations for <@{owner_id}>:**'
                    if city.title() not in description:
                        description += f'\n**{city.title()}: **'
                    description += f'{station.title()}, '
        if description[-2:] == ', ':
            description = description[:-2]            
                
    if description != '':
        if int(owner_id) in stations_coowners:
            description += f'\n**Co-owners - **'
            for coowner in stations_coowners[int(owner_id)]:
                description += f'<@{coowner}> '
    
    if description == '':
        description = f'**<@{owner_id}> has no stations.**'
        if int(owner_id) in stations_coowners:
            description += f'\n**<@{owner_id}> has co-owners - **'
            for coowner in stations_coowners[int(owner_id)]:
                description += f'<@{coowner}> '
    
    await interaction.response.send_message(description, ephemeral=True)

# Adds co-owner to all stations of interaction.user
@bot.slash_command(description='Assigns co-owner to owner.', guild_ids=[SERVER_ID], default_member_permissions=8)
async def add_coowner(
        interaction: nextcord.Interaction,
        coowner: str = SlashOption(
            name='coowner', description='Ping the co-owner or write his server name.'),
        owner: Optional[str] = SlashOption(name='owner', description='Ping the owner or write his server name. If empty defaults to you.'),):
    print(f'{interaction.user} has used add_coowner in {interaction.channel} at {curr_time()} UTC\n')

    await interaction.response.defer(ephemeral=True, with_message=True)

    if owner == None:
        owner_id = interaction.user.id
    else:
        owner_id = _get_user_id(owner)

    coowner_id = _get_user_id(coowner)

    for owner in stations_coowners:
        if str(owner_id) == str(owner):
            for coowner in stations_coowners[int(owner_id)]:
                if str(coowner_id) == str(coowner):
                    await interaction.followup.send(f"<@{coowner_id}> is already co-owner of <@{owner_id}>'s stations.", ephemeral=True, delete_after=30)
                    return

            else:
                stations_coowners[owner_id].append(coowner_id)
                database.insert_data('stations_coowners',
                                     owner_id=owner_id, coowner_id=coowner_id)
                await interaction.followup.send(f"<@{coowner_id}> is now co-owner of <@{owner_id}>'s stations.", ephemeral=True, delete_after=30)
                _update_stations_coowners()
                return

    if owner_id not in stations_coowners:
        stations_coowners[owner_id] = [coowner_id]
        database.insert_data('stations_coowners',
                             owner_id=owner_id, coowner_id=coowner_id)
        await interaction.followup.send(f"<@{coowner_id}> is now co-owner of <@{owner_id}>'s stations.", ephemeral=True, delete_after=30)
        _update_stations_coowners()
        return

# Removes given co-owner from interaction.user's stations
@bot.slash_command(description='Removes co-owner from owner.', guild_ids=[SERVER_ID], default_member_permissions=8)
async def remove_coowner(
        interaction: nextcord.Interaction,
        coowner: str = SlashOption(
            name='coowner', description='Ping the co-owner or write his server name.'),
        owner: Optional[str] = SlashOption(name='owner', description='Ping the owner or write his server name. If empty defaults to you.'),):
    print(f'{interaction.user} has used remove_coowner in {interaction.channel} at {curr_time()} UTC\n')
    await interaction.response.defer(ephemeral=True, with_message=True)

    if owner == None:
        owner_id = interaction.user.id
    else:
        owner_id = _get_user_id(owner)
    coowner_id = _get_user_id(coowner)

    # check if owner and coowner combination exists in stations_coowners
    for owner in stations_coowners:
        if str(owner_id) == str(owner):
            for coowner in stations_coowners[int(owner_id)]:
                if str(coowner_id) == str(coowner):
                    try:
                        database.delete_data(
                            'stations_coowners', where=f'WHERE owner_id = {owner_id} and coowner_id = {coowner_id}')
                        _update_stations_coowners()
                        await interaction.followup.send(f"<@{coowner_id}> is no longer co-owner of your stations.", ephemeral=True, delete_after=30)
                        return
                    except:
                        await interaction.followup.send(f"Something went wrong. Please check if you wrote the command correctly and try again. If problem keeps occuring please contact <@158643072886898688>", ephemeral=True, delete_after=30)
    await interaction.followup.send(f"Couldn't find <@{owner_id}> - <@{coowner_id}> combination. \nCheck for typos, or try checking coowners_list with /owner_stations or /display_stations", ephemeral=True, delete_after=30)

@bot.slash_command(description='Adds stations to the stations list.',guild_ids=[SERVER_ID],default_member_permissions=8)
async def add_stations(
    interaction: nextcord.Interaction,
    city: str = SlashOption(name='city',description='Chosen city',choices={
            'Fort Sterling': 'fortsterling',
            'Lymhurst': 'lymhurst',
            'Bridgewatch': 'bridgewatch',
            'Martlock': 'martlock',
            'Thetford': 'thetford',
            'Caerleon': 'caerleon'}),
    stations: str = SlashOption(name='stations',description='Write stations you want to add in this format "hunter, warrior, mage..."'),
    owner: Optional[str] = SlashOption(description="Ping the owner or write their server name. If empty, will add to your stations")):
    print(f'{interaction.user} has used add_station in {interaction.channel} at 'f'{curr_time()} UTC\n')

    await interaction.response.defer(ephemeral=True, with_message=True)

    owner_id = _get_user_id(owner) if owner else _get_user_id(interaction.user.name)

    station_list = stations.split(",")

    for i in range(len(station_list)):
        station_list[i] = station_list[i].replace(" ", "")

    invalid_message = ""
    message = ""

    for station in station_list:
        if station not in valid_stations:
            if invalid_message == "":
                invalid_message += "**Couldn't add following stations: **"
            invalid_message += f"\n{station}"

        elif (city, station, owner_id) not in database.get_data('stations',columns='DISTINCT city, station_name, owner_id'):
            database.insert_data('stations', city=city,station_name=station, owner_id=owner_id)

            if message == "":
                message += f"**Adding stations to <@{owner_id}> in {city.title()}: **\n"

            message += f"• {station.title()}\n"

        else:
            message += f'• {station.title()} is already added.\n'

    message += invalid_message

    if message != "":
        _update_stations_list()
        await interaction.followup.send(message,ephemeral=True,delete_after=30)

    else:
        await interaction.followup.send("Did not add any stations.",ephemeral=True,delete_after=30)

# Deletes chosen station in city from selected owner. If no owner provided defaults to interaction.user       
@bot.slash_command(description='Deletes stations from owner.', guild_ids=[SERVER_ID], default_member_permissions=8)
async def remove_stations(
    interaction: nextcord.Interaction,
    city: str = SlashOption(name='city', description='Chosen city', choices={
        'Fort Sterling': 'fortsterling',
       'Lymhurst': 'lymhurst',
       'Bridgewatch': 'bridgewatch',
       'Martlock': 'martlock',
       'Thetford': 'thetford',
       'Caerleon': 'caerleon'
    }),
    stations: str = SlashOption(name='station', description='Chosen stations. Write in this format "hunter, warrior, mage..."'), 
    owner: Optional[str] = SlashOption(description="Ping the owner or write down his server name, if empty will remove your stations.")): 
    print(f'{interaction.user} has used remove_stations in {interaction.channel} at {curr_time()} UTC\n')
    await interaction.response.defer(ephemeral=True, with_message=True)
    if owner == None:
        owner_id = interaction.user.id
    else:
        owner_id = _get_user_id(owner)
        
    station_list = stations.split(",")

    for i in range(len(station_list)):
        station_list[i] = station_list[i].replace(" ", "")

    message = ""
    invalid_message = ""
    removed_message = ""
    db_stations = database.get_data('stations', columns='DISTINCT city, station_name, owner_id')
    for station in station_list:
        if station not in valid_stations:
            if invalid_message == "":
                invalid_message += "**Couldn't remove following stations: **"
            invalid_message += f"\n{station}"

        elif (str(city), str(station), int(owner_id)) in db_stations:
            database.delete_data('stations', where=f'WHERE city = "{city}" AND station_name = "{station}" and owner_id = {owner_id}')

            removed_message += f"• {station.title()}\n"

        else:
            message += f'• {station.title()} owned by <@{owner_id}> in {city.title()} not found in database.\n'
    if removed_message != "":
        message += f"**Removed stations from <@{owner_id}> in {city.title()}: **\n"
        message += removed_message
    message += invalid_message

    if message != "":
        _update_stations_list()
        await interaction.followup.send(message, ephemeral=True, delete_after=30)

# Sets stations image to given city. Needs URL to IMAGE to display properly.
@bot.slash_command(description='Sets the image of specified city.', guild_ids=[SERVER_ID], default_member_permissions=8)
async def set_image(
    interaction: nextcord.Interaction, 
    city: str = SlashOption(name='city', description='Chosen city', choices={
        'Fort Sterling': 'fortsterling',
        'Lymhurst': 'lymhurst',
        'Bridgewatch': 'bridgewatch',
        'Martlock': 'martlock',
        'Thetford': 'thetford',
        'Caerleon': 'caerleon'
    }),
    image: str = SlashOption(description="Image to display. Needs to be URL to an IMAGE.")): 
    print(f'{interaction.user} has used set_image in {interaction.channel} at {curr_time()} UTC\n')
    if city.lower() in stations_images.keys():
        database.delete_data('images', where=f'WHERE city = "{city.lower()}"')
    
    database.insert_data('images', city=city.lower(), image_link = image)
    _update_stations_images() 
    await interaction.response.send_message(f"Image for {city} updated succesfully", ephemeral=True, delete_after=30)         

# Deletes given amount of messages from interaction.channel
@bot.slash_command(description="Bulk deletes messages from current channel.", guild_ids=[SERVER_ID], default_member_permissions=8)
async def delete_messages(
    interaction: nextcord.Interaction, 
    amount: int = SlashOption(description="Amount of messages to delete.")):
    print(f'{interaction.user} has used delete_messages in {interaction.channel} at {curr_time()} UTC\n')
    if amount > 100:
        await interaction.response.send_message(f"Amount needs to be less than 100.", ephemeral=True, delete_after=5) 
    else:
        await interaction.response.send_message(f"Deleting {amount} messages.", ephemeral=True, delete_after=5)
        await interaction.channel.purge(limit = amount) 
    
# TDeveloping test command         
@bot.slash_command(description="Command for testing. Don't use it. Can do nothing, or can break everything.", guild_ids=[SERVER_ID], default_member_permissions=8)
async def test_command(interaction: nextcord.Interaction):
    buttonCog.parsed = False
        
if __name__ == '__main__':

    database.connect('stations.db')
    database.create_table('stations_coowners', [('owner_id', 'INTEGER'), ('coowner_id', 'INTEGER')])
    database.create_table('stations', [('city', 'TEXT'), ('station_name', 'TEXT'), ('owner_id', 'INTEGER')])
    database.create_table('images', [('city', 'TEXT UNIQUE'), ('image_link', 'TEXT')])
    database.create_table('muted', [('user_id', 'TEXT'), ('date', 'TEXT'), ('reason', 'TEXT'), ('length', 'TEXT')])
    
    taskCog = TaskCog(bot)
    buttonCog = ButtonCog(bot)
    mutedCog = MutedCog(bot)

    
    bot.add_cog(buttonCog)
    bot.add_cog(taskCog)
    bot.add_cog(mutedCog)

    bot.run(TOKEN)
    

    
    
