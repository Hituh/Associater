import os
import nextcord
import datetime
import pytz

from typing import Optional
from nextcord import Interaction, SlashOption, Colour
from nextcord.ext import commands
from cogs.bgtasks import TaskCog
from cogs.extras import ExtrasCog
from cogs.buttons import ButtonCog
from database import database
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
SERVER_ID = int(os.getenv('TESTSERVER_ID'))
TOKEN = os.getenv('DISCORD_TOKEN')


intents = nextcord.Intents(members = True, emojis = True, reactions = True, guilds = True, messages = True, message_content = True)
bot = commands.Bot(intents=intents)

@bot.event
async def on_ready():
    await _prepare_variables()
    global emojis_array
    guild = bot.get_guild(SERVER_ID)
    emojis_array = await guild.fetch_emojis()
    
    print(f'        {bot.user} has connected to Discord!\n        Currently it is connected to the following servers:')
    for guild in bot.guilds:
        print('       ',guild)
    
    
valid_cities = ['bridgewatch', 'caerleon', 'sterling', 'lymhurst', 'martlock', 'thetford']
valid_stations = ['alchemy', 'butcher', 'cook', 'hunter', 'lumbermill', 'mage', 'mill', 'saddler', 'smelter', 'stonemason', 'tanner', 'toolmaker', 'warrior', 'weaver']
stations_images = {}
stations_list = {}
stations_coowners_list = {}
emojis_array = []
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
    colors = {'sterling': 0xFFFFFF, 'lymhurst': Colour.green(), 'bridgewatch': Colour.orange(), 'martlock': Colour.blue(), 'thetford': Colour.purple(), 'caerleon': Colour.red()}
    return colors.get(city)

#Updates in-code station owners array
def _update_stations_list():
    global stations_list
    stations_list = {}
    for city, station_name, owner_id in database.get_data('stations', columns='DISTINCT city, station_name, owner_id'):
        stations_list.setdefault(city, {}).setdefault(station_name, []).append(owner_id)
    buttonCog.parsed = False
    
# Updates in-code station co-owners array
def _update_stations_coowners_list():
    global stations_coowners_list
    stations_coowners_list = {}
    for city, station_name, owner_id, coowner_id in database.get_data('stations_coowners', columns='DISTINCT city, station_name, owner_id, coowner_id'):
        stations_coowners_list.setdefault(city, {}).setdefault(station_name, {}).setdefault(owner_id, []).append(coowner_id)
    buttonCog.parsed = False
    
# Updates station image in database      
def _update_stations_images():
    global stations_images
    stations_images = dict(database.get_data('images', columns='DISTINCT city, image_link'))
    buttonCog.parsed = False

# Initializing function, calling all functions to prepare variables for the bot
async def _prepare_variables():
    await bot.wait_until_ready()
    _update_stations_list()
    _update_stations_coowners_list()
    _update_stations_images()  
    _get_autorequest_channels()

#Returns user id. Takes user class or user name as input.
def _get_user_id(value):
    guild = bot.get_guild(SERVER_ID)
    user_id = next((int(value[2:-1]) for member in guild.members if str(member) == value), None)
    if user_id is None:
        user_id = next((member.id for member in guild.members if member.name.lower() == value.lower()), None)
    return user_id

   
    
#Displays embed of current stations in chosen city
@bot.slash_command(description='Shows information about stations in specified city.', guild_ids=[SERVER_ID], default_member_permissions=8)
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
@bot.slash_command(description='Displays all stations from a specific owner.', guild_ids=[SERVER_ID], default_member_permissions=8)
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
@bot.slash_command(description='Adds a station to the list of stations.', guild_ids=[SERVER_ID], default_member_permissions=8)
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
@bot.slash_command(description='Adds co-owners to your stations.', guild_ids=[SERVER_ID], default_member_permissions=8)
async def add_coowner(
    interaction: nextcord.Interaction, 
    coowner: str = SlashOption(name='coowner', description='Ping your desired co-owner')):
    print(f'{interaction.user} has used add_coowner in {interaction.channel} at {datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")} UTC\nInteraction message : {interaction.data}')
    
    coowner_id = _get_user_id(coowner)
    guild = bot.get_guild(SERVER_ID)
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
@bot.slash_command(description='Adds co-owners to your stations.', guild_ids=[SERVER_ID], default_member_permissions=8)
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
@bot.slash_command(description='Delete as station from owner', guild_ids=[SERVER_ID], default_member_permissions=8)
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
@bot.slash_command(description='Sets the image of specified city', guild_ids=[SERVER_ID], default_member_permissions=8)
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


#Mass delete messages
@bot.slash_command(description="Deletes given amount of messages from current channel.", guild_ids=[SERVER_ID], default_member_permissions=8)  
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
@bot.slash_command(description="Sends close button and done message to all threads older than given amount in the channel.", guild_ids=[SERVER_ID], default_member_permissions=8)
async def set_all_done(
    interaction: nextcord.Interaction,
    amount: int = SlashOption(description="Threads age in seconds.")): 

    print(f'{interaction.user} has used set_done in {interaction.channel} at {datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")} UTC\nInteraction message : {interaction.data}')

    counter = 0

    # Get the list of threads in the channel or its parent, depending on whether the channel is a private thread or not
    threads_list = interaction.channel.parent.threads if str(interaction.channel.type) == 'private_thread' else interaction.channel.threads

    
    # Loop through the threads and check if they are older than the given amount
    for thread in threads_list:
        diff = int(((datetime.datetime.utcnow().replace(tzinfo=pytz.utc)) - (thread.created_at - datetime.timedelta(seconds=0))).total_seconds())
        if diff > amount and not thread.archived and '✔ ' not in thread.name:
            # Set the thread's auto-archive duration to 24 hours
            await thread.edit(auto_archive_duration=1440, name = '✔  ' + thread.name)

            # Send a finish message to the thread's owner
            first_message = await thread.history(oldest_first = True, limit=1).flatten()
            # button = ButtonCog.ButtonFinish()      
            # await thread.send(f"<@{first_message[0].mentions[0].id}> your request have been fulfilled.\nIf something's missing ping owners.\nIf everything is correct press the button below to close the thread.\nThread will automatically close after 24 hours.", view=button)
            
            # Set the button's message ID to the ID of the message that was just sent
            button_id = await thread.history(limit=1).flatten()
            # button.message = button_id[0]
            counter += 1             

    # Send a response message indicating the number of threads that were finished, or that none were found
    if counter != 0:
        await interaction.response.send_message(f"Sent finished message to {counter} threads older than {amount} seconds.", ephemeral=True, delete_after=5)
    else:
        await interaction.response.send_message(f"Didn't find any unfinished threads older than {amount} seconds.", ephemeral=True, delete_after=5)

@bot.slash_command(description="Command for testing.", guild_ids=[SERVER_ID], default_member_permissions=8)
async def test_command(interaction: nextcord.Interaction):
    buttonCog.parsed = False
        
if __name__ == '__main__':

    database.connect('stations.db')
    database.create_table('stations_coowners', [('city', 'TEXT'), ('station_name', 'TEXT'), ('owner_id', 'INTEGER'), ('coowner_id', 'INTEGER')])
    database.create_table('stations', [('city', 'TEXT'), ('station_name', 'TEXT'), ('owner_id', 'INTEGER')])
    database.create_table('images', [('city', 'TEXT UNIQUE'), ('image_link', 'TEXT')])
    
    taskCog = TaskCog(bot)
    buttonCog = ButtonCog(bot)
    extrasCog = ExtrasCog(bot)
    
    bot.add_cog(extrasCog)
    bot.add_cog(buttonCog)
    bot.add_cog(taskCog)
    

    _update_stations_list()
    _update_stations_images()
    _update_stations_coowners_list()
    
    bot.run(os.getenv('BOT_TOKEN'))
    

    
    
