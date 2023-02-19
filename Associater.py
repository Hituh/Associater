import os
import nextcord
import discord
import logging
import datetime

from typing import Optional
from nextcord import Interaction, SlashOption, Colour
from nextcord.ext import commands, tasks

from aux_libraries import database
import pandas as pd

from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = nextcord.Intents.all()
intents.members = True
bot = commands.Bot(intents=discord.Intents.all())

logger = logging.getLogger('nextcord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='nextcord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

@bot.event
async def on_ready():
    print(f'        {bot.user} has connected to Discord!\n        Currently it is connected to the following servers:')
    for guild in bot.guilds:
        print('       ',guild)
    
valid_cities = ['bridgewatch', 'caerleon', 'sterling', 'lymhurst', 'martlock', 'thetford']
valid_stations = ['alchemy', 'butcher', 'cook', 'hunter', 'lumbermill', 'mage', 'mill', 'saddler', 'smelter', 'stonemason', 'tanner', 'toolmaker', 'warrior', 'weaver']
stations_images = {}
stations_list = {}

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
        
def _update_stations_images():
    global stations_images
    stations_images = {}
    images = database.get_data('images', columns='DISTINCT city, image_link')
    for image in images:
        city = image[0]
        image_link = image[1]
        stations_images[city] = image_link
    
@bot.slash_command(description='Shows information about stations in specified city', guild_ids=[int(os.getenv('TESTSERVER_ID'))], default_member_permissions=8)
async def display_stations(
    interaction: nextcord.Interaction, 
    city: str = SlashOption(name='city', description='Chosen city to display', choices={
        'Sterling': 'sterling',
        'Lymhurst': 'lymhurst',
        'Bridgewatch': 'bridgewatch',
        'Martlock': 'martlock',
        'Thetford': 'thetford',
        'Caerleon': 'caerleon'
    })):
    channel = interaction.channel
    print(f'{interaction.user} has used display_stations in {interaction.channel} at {datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")} UTC')
    if city in stations_images:
        await interaction.response.send_message(f"*You have selected {city} to display, the full message will be shown shortly*", ephemeral=True, delete_after=15)         
        image = stations_images[city.lower()]
        
        description = (f'**Avaiable shops in {city.title()}**\n')
        for station in stations_list[city]:
            station_name = station
            description += (f'\n{station_name} -')
            for owner in stations_list[city][station]:
                description += (f' <@{str(owner)}>')
        
        if city == 'sterling':
            embedColor = Colour.white()
        if city == 'lymhurst':
            embedColor = Colour.green()
        if city == 'bridgewatch':
            embedColor = Colour.orange()
        if city == 'martlock':
            embedColor = Colour.blue()
        if city == 'thetford':
            embedColor = Colour.purple()
        if city == 'caerleon':
            embedColor = Colour.red()

        em = nextcord.Embed(
                description=description,
                color=embedColor
            )
        em.set_author(name=f'**Please use /request for requesting**\n')
        em.set_image(image)
        em.set_footer(text=f'Updated at {datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")} UTC\n',)
        await channel.send(embed=em)
    else:
        await interaction.response.send_message(f"{city} not found in the database, please contact Hituh", ephemeral=True, delete_after=5)         

@bot.slash_command(description='Displays all stations from a specific owner.', guild_ids=[int(os.getenv('TESTSERVER_ID'))], default_member_permissions=8)
async def owner_stations(
    interaction: nextcord.Interaction, 
    owner: Optional[str] = SlashOption(description="Owner name, if empty will display your stations")):
    print(f'{interaction.user} has used owner_stations in {interaction.channel} at {datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")} UTC')

    if owner == None:
        owner = interaction.user
        owner_id = str(owner.id)
    else:
        owner_id = str(owner)[2:-1]
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
        await interaction.response.send_message(f"{owner_list}```", ephemeral=True, delete_after=300)         
    else:
        await interaction.response.send_message(f'No stations found for <@{owner_id}>', delete_after=300)    

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
        "Toolmater" : 'toolmaker', 
        "Warrior's Forge" : 'warrior', 
        "Weaver" : 'weaver'
    }), 
    owner: Optional[str] = SlashOption(description="Owner name. If empty will add to your stations")):
    print(f'{interaction.user} has used add_station in {interaction.channel} at {datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")} UTC')
    
    if owner == None:
        owner = interaction.user
        owner_id = str(owner.id)
    else:
        owner_id = str(owner)[2:-1]
        
    if (str(city), str(station), int(owner_id)) not in database.get_data('stations', columns='DISTINCT city, station_name, owner_id'):
        database.insert_data('stations', city=city, station_name=station, owner_id=owner_id)
        _update_stations_list()
        await interaction.response.send_message(f"{station.title()} added for <@{owner_id} at {city.title()}>", ephemeral=True, delete_after=300)         
    else:
        await interaction.response.send_message(f'{station.title()} is already added for <@{owner_id}> at {city.title()}.', ephemeral=True, delete_after=300)
    
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
        "Toolmater" : 'toolmaker', 
        "Warrior's Forge" : 'warrior', 
        "Weaver" : 'weaver'
    }), 
    owner: Optional[str] = SlashOption(description="Owner name. If empty will remove your stations")): 
    print(f'{interaction.user} has used delete_station in {interaction.channel} at {datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")} UTC')
 
    if owner == None:
        owner = interaction.user
        owner_id = str(owner.id)
    else:
        owner_id = str(owner)[2:-1]
    if (str(city), str(station), int(owner_id)) in database.get_data('stations', columns='DISTINCT city, station_name, owner_id'):
        database.delete_data('stations', where=f'WHERE city = "{city}" AND station_name = "{station}" and owner_id = {owner_id}')
        _update_stations_list()
        await interaction.response.send_message(f"{station.title()} removed from <@{owner_id}> at {city.title()}", ephemeral=True, delete_after=300)         
    else:
        await interaction.response.send_message(f'{station.title()} owned by <@{owner_id}> in {city.title()} not found in database.', ephemeral=True, delete_after=300)
      
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
    image: str = SlashOption(description="Image to display")): 
    print(f'{interaction.user} has used set_image in {interaction.channel} at {datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")} UTC')
    if city.lower() in stations_images.keys():
        database.delete_data('images', where=f'WHERE city = "{city.lower()}"')
    
    database.insert_data('images', city=city.lower(), image_link = image)
    _update_stations_images() 
    await interaction.response.send_message(f"Image for {city} updated succesfully", ephemeral=True, delete_after=300)         

    
if __name__ == '__main__':

    database.connect('stations.db')
    
    database.create_table('stations', [('city', 'TEXT'), ('station_name', 'TEXT'), ('owner_id', 'INTEGER')])
    database.create_table('images', [('city', 'TEXT UNIQUE'), ('image_link', 'TEXT')])

    _update_stations_list()
    _update_stations_images()
    bot.run(os.getenv('BOT_TOKEN'))