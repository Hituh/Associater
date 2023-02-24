import os
import nextcord
import discord
import logging
import datetime

from typing import Optional
from nextcord import Interaction, SlashOption, Colour
from nextcord.ext import commands, tasks
from nextcord.utils import get
from pyparsing import List
import pytz

from aux_libraries import database
import pandas as pd

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
    city: str = SlashOption(name='city', description='Choose city to display stations info.', choices={
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
        description = (f'**Avaiable shops in {city.title()}**\n*For more info check <#1076945622185295912>*')
        await interaction.response.send_message(f"*You have selected {city} to display, the full message will be shown shortly*", ephemeral=True, delete_after=15)         
        
        #Creates owners and co-owners string to display in embed
        for station in stations_list[city]:
            description += (f'\n**{station.title()}**')
            for owner in stations_list[city][station]:
                description += (f'\nOwner - <@{str(owner)}>') 
                if city in stations_coowners_list and station in stations_coowners_list[city] and owner in stations_coowners_list[city][station]:
                    description += (f' Co-owners -')
                    for coowner in stations_coowners_list[city][station][owner]:
                        description += (f' <@{str(coowner)}>')  
        
        #Embed creation          
        embedColor = _set_embed_colour(city)
        em = nextcord.Embed(
                description=description,
                color=embedColor)
        em.set_author(name=f'Please use /request for requesting\n')
        em.set_image(image)
        em.set_footer(text=f'Updated at {datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")} UTC\n',)
        await channel.send(embed=em)
        
    elif city not in stations_images:
        await interaction.response.send_message(f"{city} doesn't have image set, please set image for the city and try again. If problem keeps appearing please contact Hituh", ephemeral=True, delete_after=5)         
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

    if owner == None:
        owner_id = _get_user_id(interaction.user.name)
    else:
        owner_id = _get_user_id(owner)
    owner_list = f'Stations list for {owner}\n```'
    stations = False
    for city in stations_list.keys():
        for station in stations_list[city].keys():
            for owner in stations_list[city][station]:
                if str(owner) == str(owner_id):
                    stations = True
                    owner_list += f'{city} -> {station}\n'
        owner_list += '\n'
    if stations:
        await interaction.response.send_message(f"{owner_list}```", ephemeral=True, delete_after=30)         
    else:
        await interaction.response.send_message(f'No stations found for <@{owner_id}>', delete_after=30)    

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
    
    if owner == None:
        owner_id = _get_user_id(interaction.user.name)
    else:
        owner_id = _get_user_id(owner)
        
    if (str(city), str(station), int(owner_id)) not in database.get_data('stations', columns='DISTINCT city, station_name, owner_id'):
        database.insert_data('stations', city=city, station_name=station, owner_id=owner_id)
        _update_stations_list()
        await interaction.response.send_message(f"{station.title()} added for <@{owner_id}> at {city.title()}", ephemeral=True, delete_after=30)         
    else:
        await interaction.response.send_message(f'{station.title()} is already added for <@{owner_id}> at {city.title()}.', ephemeral=True, delete_after=30)

#Add station to interaction.user
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
 
    if owner == None:
        owner_id = _get_user_id(interaction.user.name)
    else:
        owner_id = _get_user_id(owner)
        
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
        nickname: str = SlashOption(description="Your in-game nickname. After writing your name press TAB to see other options."),
        guildname: Optional[str] = SlashOption(description="If you're requesting for a guild, please write your full guild name."),
        alliancename: Optional[str] = SlashOption(description="If you're requesting for an alliance, please write your full alliance name."),
        alchemist: Optional[str] = SlashOption(description="Select this option and then select 'Yes I want this station' to add Alchemist's Lab to your request.", choices={'Yes I want this station'}),
        butcher: Optional[str] = SlashOption(description="Select this option and then select 'Yes I want this station' to add Butcher to your request.", choices={'Yes I want this station'}),
        cook: Optional[str] = SlashOption(description="Select this option and then select 'Yes I want this station' to add Cook to your request.", choices={'Yes I want this station'}),
        hunter: Optional[str] = SlashOption(description="Select this option and then select 'Yes I want this station' to add Hunter's Lodge to your request.", choices={'Yes I want this station'}),
        lumbermill: Optional[str] = SlashOption(description="Select this option and then select 'Yes I want this station' to add Lumbermill to your request.", choices={'Yes I want this station'}),
        mage: Optional[str] = SlashOption(description="Select this option and then select 'Yes I want this station' to add Mage's Tower to your request.", choices={'Yes I want this station'}),
        mill: Optional[str] = SlashOption(description="Select this option and then select 'Yes I want this station' to add Mill to your request.", choices={'Yes I want this station'}),
        saddler: Optional[str] = SlashOption(description="Select this option and then select 'Yes I want this station' to add Saddler to your request.", choices={'Yes I want this station'}),
        smelter: Optional[str] = SlashOption(description="Select this option and then select 'Yes I want this station' to add Smelter to your request.", choices={'Yes I want this station'}),
        stonemason: Optional[str] = SlashOption(description="Select this option and then select 'Yes I want this station' to add Stonemason to your request.", choices={'Yes I want this station'}),
        tanner: Optional[str] = SlashOption(description="Select this option and then select 'Yes I want this station' to add Tanner to your request.", choices={'Yes I want this station'}),
        toolmaker: Optional[str] = SlashOption(description="Select this option and then select 'Yes I want this station' to add Toolmaker to your request.", choices={'Yes I want this station'}),
        warrior: Optional[str] = SlashOption(description="Select this option and then select 'Yes I want this station' to add Warrior's Forge to your request.", choices={'Yes I want this station'}),
        weaver: Optional[str] = SlashOption(description="Select this option and then select 'Yes I want this station' to add Weaver to your request.", choices={'Yes I want this station'}),      
        ):
    print(f'{interaction.user} has used request in {interaction.channel} at {datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")} UTC\nInteraction message : {interaction.data}')
    channel = interaction.channel.id
    
    #Finding if user has already made thread
    threads_in_channel = interaction.channel.threads
    thread_found = None
    for thread in threads_in_channel:
        if interaction.user.name in thread.name and thread.archived == False:
            thread_found = thread
    
    #Correct channel check        
    if(str(channel) not in request_channels):
        r_channels = ''
        for channel in request_channels:
            r_channels += f"<#{channel}> "
        await interaction.response.send_message(f"You shouldn't use that command here. Please use it in your city of choice in {r_channels}", ephemeral=True, delete_after=30)
    
    else:
        #Creating request array
        requests = []
        city = _get_city_by_id(channel)
        if(alchemist != None): requests.append('alchemy')
        if(butcher != None): requests.append('butcher')
        if(cook != None): requests.append('cook')
        if(hunter != None): requests.append('hunter')
        if(lumbermill != None): requests.append('lumbermill')
        if(mage != None): requests.append('mage')
        if(mill != None): requests.append('mill')
        if(saddler != None): requests.append('saddler')
        if(smelter != None): requests.append('smelter')
        if(stonemason != None): requests.append('stonemason')
        if(tanner != None): requests.append('tanner')
        if(toolmaker != None): requests.append('toolmaker')
        if(warrior != None): requests.append('warrior')
        if(weaver != None): requests.append('weaver')
        
        #Requested station availability check
        request_string = ''
        are_stations_available = True
        stations_not_avaiable = ''
        for request in requests:
            if(str(request) not in stations_list[city]):
                are_stations_available = False
                stations_not_avaiable += f'{request.title()} '
            request_string += f'{request.title()} '
        if not requests:
            await interaction.response.send_message(f"You need to select at least one station.", ephemeral=True, delete_after=30) 
        elif(requests and are_stations_available == False):
            await interaction.response.send_message(f"{stations_not_avaiable}are currently not avaiable in {city.title()}. Please check the list of avaiable stations in the city and try again.", ephemeral=True, delete_after=30) 
        
        #Request is proper
        elif(requests and are_stations_available == True):
            #Creating new thread or adding new embed to already existing thread made by interaction user
            if thread_found == None:
                await interaction.response.send_message(f"You are requesting {request_string}in {city.title()}, private thread will be opened shortly.", ephemeral=True, delete_after=30)
                thread = await interaction.channel.create_thread(name=f'{interaction.user.name} request', message=None, auto_archive_duration=60, type=None)
            else: 
                await interaction.response.send_message(f"This request has been added to your current one. Here is your thread <#{thread.id}> ", ephemeral=True, delete_after=60)
                thread = thread_found
                
            #Adding to thread
            await thread.add_user(interaction.user)
            guild = bot.get_guild(int(os.getenv('TESTSERVER_ID')))
            owner_ids = []
            for request in requests:
                if(city in stations_list and request in stations_list[city] and stations_list[city][request] not in owner_ids):
                    for owner in stations_list[city][request]:
                        owner_ids.append(owner)
                        if city in stations_coowners_list and request in stations_coowners_list[city] and owner in stations_coowners_list[city][request]:
                            for coowner in stations_coowners_list[city][request][owner]:
                                if coowner not in owner_ids:
                                    owner_ids.append(coowner) 
            for id in owner_ids:
                try:
                    member = guild.get_member(id)
                    await thread.add_user(member)
                except: 
                    await thread.send(f"I couldn't find <@{id}> in the server. If this not intentional, please contant <@158643072886898688>")
                    
            #Embed creation
            embedColor = _set_embed_colour(city)
            description = f"Associate request in **{city}**. Stations:\n"
            description = f"\nStations:\n"
            for request in requests:
                description += f"{request.title()}\n"
            em = nextcord.Embed(
                    description=description,
                    color=embedColor)
            for request in requests:
                description += f"{request.title()}\n"
            if(alliancename == None and guildname == None):
                em.set_author(name=f'Request made by {interaction.user.name} for player {nickname}', icon_url=f'{interaction.user.avatar}')
            if(alliancename == None and guildname != None):
                em.set_author(name=f'Request made by {interaction.user.name} for guild {guildname}', icon_url=f'{interaction.user.avatar}')
            if(alliancename != None):
                em.set_author(name=f'Request made by {interaction.user.name} for alliance {alliancename}', icon_url=f'{interaction.user.avatar}')
            em.set_footer(text=f'Request made at: {datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")} UTC\n',)
            await thread.send(embed=em)
   
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

#Replies to all active threads in channel. To be improved to include close button and 24h auto-archive timer
@bot.slash_command(description="Replies to all threads in the city.", guild_ids=[int(os.getenv('TESTSERVER_ID'))], default_member_permissions=8)  
async def reply_to_threads(
    interaction: nextcord.Interaction, 
    message: str = SlashOption()):
    threads_in_channel = interaction.channel.threads
    for thread in threads_in_channel:
        await thread.send(f"{message}")
    
#Archives threads older than given amount of seconds
@bot.slash_command(description="Archives all threads older than given amount of seconds.", guild_ids=[int(os.getenv('TESTSERVER_ID'))], default_member_permissions=8)  
async def archive_done_threads(
    interaction: nextcord.Interaction, 
    amount: int = SlashOption(description="Threads age in seconds.")):  
    print(f'{interaction.user} has used archive_done_threads in {interaction.channel} at {datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")} UTC\nInteraction message : {interaction.data}')
    threads_in_channel = interaction.channel.threads
    counter = 0
    for thread in threads_in_channel:
        diff = int(((datetime.datetime.utcnow().replace(tzinfo=pytz.utc)) - (thread.created_at - datetime.timedelta(seconds=0))).total_seconds())
        if diff > amount and thread.archived == False:
            await thread.edit(archived = True)
            counter += 1
    if counter != 0:
        await interaction.response.send_message(f"Done archiving {counter} threads older than {amount} seconds from current channel.", ephemeral=True, delete_after=5)
    else:
        await interaction.response.send_message(f"Didn't find any threads older than {amount} seconds.", ephemeral=True, delete_after=5)
         
if __name__ == '__main__':

    database.connect('stations.db')
    database.create_table('stations_coowners', [('city', 'TEXT'), ('station_name', 'TEXT'), ('owner_id', 'INTEGER'), ('coowner_id', 'INTEGER')])
    database.create_table('stations', [('city', 'TEXT'), ('station_name', 'TEXT'), ('owner_id', 'INTEGER')])
    database.create_table('images', [('city', 'TEXT UNIQUE'), ('image_link', 'TEXT')])

    _update_stations_list()
    _update_stations_images()
    _update_stations_coowners_list()

            
    bot.run(os.getenv('BOT_TOKEN'))