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

def _update_stations_list():
    global stations_list
    stations_list = {}
    stations = database.get_data('stations', columns='DISTINCT city, station_name, owner_id')
    stations_coowners = database.get_data('stations_coowners', columns='DISTINCT city, station_name, owner_id, coowner_id')

    for station in stations:
        city = station[0]
        station_name = station[1]
        owner_id = station[2]
        
        if city not in stations_list.keys():
            stations_list[city] = {}
        if station_name not in stations_list[city].keys():
            stations_list[city][station_name] = []
        stations_list[city][station_name].append(owner_id)
    
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
        
def _update_stations_images():
    global stations_images
    stations_images = {}
    images = database.get_data('images', columns='DISTINCT city, image_link')
    for image in images:
        city = image[0]
        image_link = image[1]
        stations_images[city] = image_link
  
def _get_user_id(value):
    guild = bot.get_guild(int(os.getenv('TESTSERVER_ID')))
    if(value[0] == '<'):
        user_id = guild.get_member(int(value[2:-1])).id
    else:
        for member in guild.members:
            if member.name.lower() == value.lower():
                user_id = member.id
    return user_id
      
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
    if city in stations_images and city in stations_list.keys(): 
        image = stations_images[city.lower()]
        description = (f'**Avaiable shops in {city.title()}**\n*For more info check <#1076945622185295912>*')
        await interaction.response.send_message(f"*You have selected {city} to display, the full message will be shown shortly*", ephemeral=True, delete_after=15)         
        for station in stations_list[city]:
            description += (f'\n**{station.title()}**')
            for owner in stations_list[city][station]:
                description += (f'\nOwner - <@{str(owner)}>') 
                if city in stations_coowners_list and station in stations_coowners_list[city] and owner in stations_coowners_list[city][station]:
                    description += (f' Co-owners -')
                    for coowner in stations_coowners_list[city][station][owner]:
                        description += (f' <@{str(coowner)}>')            
        embedColor = _set_embed_colour(city)

        em = nextcord.Embed(
                description=description,
                color=embedColor
            )
        em.set_author(name=f'Please use /request for requesting\n')
        em.set_image(image)
        em.set_footer(text=f'Updated at {datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")} UTC\n',)
        await channel.send(embed=em)
    elif city not in stations_images:
        await interaction.response.send_message(f"{city} doesn't have image set, please set image for the city and try again. If problem keeps appearing please contact Hituh", ephemeral=True, delete_after=5)         

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
 
@bot.slash_command(description='Adds co-owners to your stations.', guild_ids=[int(os.getenv('TESTSERVER_ID'))], default_member_permissions=8)
async def remove_coowner(
    interaction: nextcord.Interaction, 
    coowner: str = SlashOption(name='coowner', description='Ping your desired co-owner')):
    print(f'{interaction.user} has used remove_coowner in {interaction.channel} at {datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")} UTC\nInteraction message : {interaction.data}')
    coowner_id = _get_user_id(coowner)
    try:
        database.delete_data('stations_coowners', where=f'WHERE owner_id = {interaction.user.id}') 
        _update_stations_coowners_list() 
        await interaction.response.send_message(f"<@{coowner_id}> has been removed as coowner of your stations.", ephemeral=True, delete_after=30)
    except:
        await interaction.response.send_message(f"Something went wrong. Please check if you wrote the command correctly and try again. If problem keeps occuring please contact <@158643072886898688>", ephemeral=True, delete_after=30)
        
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
    if(str(channel) not in request_channels):
        r_channels = ''
        for channel in request_channels:
            r_channels += f"<#{channel}> "
        await interaction.response.send_message(f"You shouldn't use that command here. Please use it in your city of choice in {r_channels}", ephemeral=True, delete_after=30)
    else:
        requests = []
        if(str(channel) == "1076824842155860059"): city = 'lymhurst'
        if(str(channel) == "1076824842155860060"): city = 'bridgewatch'
        if(str(channel) == "1076824842155860061"): city = 'martlock'
        if(str(channel) == "1076824842155860062"): city = 'thetford'
        if(str(channel) == "1076824842155860063"): city = 'sterling'
        if(str(channel) == "1076824842155860064"): city = 'caerleon'
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
        #Thread created
        elif(requests and are_stations_available == True):
            await interaction.response.send_message(f"You are requesting {request_string}in {city.title()}, private thread will be opened shortly.", ephemeral=True, delete_after=30)
            thread = await interaction.channel.create_thread(name=f'{interaction.user.name} request', message=None, auto_archive_duration=60, type=None)
            await thread.add_user(interaction.user)
            guild = bot.get_guild(int(os.getenv('TESTSERVER_ID')))
            owner_ids = []
            for station in stations_list[city].keys():
                if(station in requests and stations_list[city][station] not in owner_ids):
                    for owner in stations_list[city][station]:
                            owner_ids.append(owner)
                        
            for owner in owner_ids:
                try:
                    member = guild.get_member(owner)
                    await thread.add_user(member)
                except: 
                    await thread.send(f"I couldn't find <@{owner}> in the server. If this not intentional, please contant <@158643072886898688>")
            #Embed creation
            embedColor = _set_embed_colour(city)
            description = f"Associate request for **{city}**. Stations:\n"
            for request in requests:
                description += f"{request.title()}\n"
            if(alliancename == None and guildname == None):
                description += f"Request for player {nickname}\n"
            if(alliancename == None and guildname != None):
                description += f"Request for guild {guildname}\n"
            if(alliancename != None):
                description += f"Request for alliance {alliancename}\n"   
            em = nextcord.Embed(
                    description=description,
                    color=embedColor
                )
            em.set_author(name=f'Request made by: {interaction.user.name}', icon_url=f'{interaction.user.avatar}')
            em.set_footer(text=f'Request made at: {datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")} UTC\n',)
            await thread.send(embed=em)
   
@bot.slash_command(description="Request for associate", guild_ids=[int(os.getenv('TESTSERVER_ID'))])
async def get_userid(
    interaction: nextcord.Interaction, 
    nickname: str = SlashOption(description="Your in-game nickname. After writing your name press TAB to see other options.")):
    await interaction.response.send_message(f"{_get_user_id(nickname)}", ephemeral=True, delete_after=30)         
        
if __name__ == '__main__':

    database.connect('stations.db')
    database.create_table('stations_coowners', [('city', 'TEXT'), ('station_name', 'TEXT'), ('owner_id', 'INTEGER'), ('coowner_id', 'INTEGER')])
    database.create_table('stations', [('city', 'TEXT'), ('station_name', 'TEXT'), ('owner_id', 'INTEGER')])
    database.create_table('images', [('city', 'TEXT UNIQUE'), ('image_link', 'TEXT')])

    _update_stations_list()
    _update_stations_images()
    _update_stations_coowners_list()
    
    
            
    bot.run(os.getenv('BOT_TOKEN'))