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
SERVER_ID = int(os.getenv("TESTSERVER_ID"))
TOKEN = os.getenv("BOT_TOKEN")

logger = logging.getLogger("nextcord")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="nextcord.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)

intents = nextcord.Intents(
    members=True,
    emojis=True,
    reactions=True,
    guilds=True,
    messages=True,
    message_content=True,
)
bot = commands.Bot(intents=intents)


@bot.event
async def on_ready():
    await _prepare_variables()
    global emojis
    guild = bot.get_guild(SERVER_ID)
    emojis = await guild.fetch_emojis()

    print(
        f"        {bot.user} has connected to Discord!\n        Currently it is connected to the following servers:"
    )
    for guild in bot.guilds:
        print("       ", guild)


valid_cities = [
    "bridgewatch",
    "caerleon",
    "fortsterling",
    "lymhurst",
    "martlock",
    "thetford",
]
valid_stations = [
    "alchemy",
    "butcher",
    "cook",
    "hunter",
    "lumbermill",
    "mage",
    "mill",
    "saddler",
    "smelter",
    "stonemason",
    "tanner",
    "toolmaker",
    "warrior",
    "weaver",
]
stations_images = {}
stations = {}
stations_coowners = {}
emojis = []
request_channels = []


# Returns preformatted current time value
def curr_time():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d, %H:%M")


# Finding all autorequest channels in guild. Channels need to have 'autorequest' in their name
def _get_autorequest_channels():
    global request_channels
    guild = bot.get_guild(SERVER_ID)
    channels_found = False
    for channel in guild.text_channels:
        if "autorequest" in channel.name:
            if channels_found:
                print(channel.name)
                request_channels.append(channel.id)
            else:
                print("Autorequest channels found:")
                print(channel.name)
                request_channels.append(channel.id)
                channels_found = True


# Returns embed colour based on city name
def _set_embed_colour(city):
    colors = {
        "fortsterling": 0xFFFFFF,
        "lymhurst": Colour.green(),
        "bridgewatch": Colour.orange(),
        "martlock": Colour.blue(),
        "thetford": Colour.purple(),
        "caerleon": Colour.red(),
    }
    return colors.get(city)


# Updates in-code station owners array
def _update_stations_list():
    global stations
    stations = {}

    for city, station_name, owner_id in database.get_data(
        "stations", columns="DISTINCT city, station_name, owner_id"
    ):
        stations.setdefault(city, {}).setdefault(station_name, []).append(owner_id)
    buttonCog.stations_list = stations


# Updates in-code station co-owners array
def _update_stations_coowners():
    global stations_coowners
    stations_coowners = {}
    for owner_id, coowner_id in database.get_data(
        "stations_coowners", columns="DISTINCT owner_id, coowner_id"
    ):
        stations_coowners.setdefault(owner_id, []).append(coowner_id)
    buttonCog.stations_coowners_list = stations_coowners


# Updates station image in database
def _update_stations_images():
    global stations_images
    stations_images = {}
    for city, image_link in database.get_data(
        "images", columns="DISTINCT city, image_link"
    ):
        stations_images.setdefault(city, []).append(image_link)
    buttonCog.stations_images = stations_images


# Initializing function, calling all functions to prepare variables for the bot
async def _prepare_variables():
    await bot.wait_until_ready()
    _get_autorequest_channels()
    _update_stations_list()
    _update_stations_coowners()
    _update_stations_images()


# Returns user id. Takes user class or user name as input.
def _get_user_id(value):
    user_id = None
    if len(value[2:-1]) == 18 and value[2:-1].isdigit():
        user_id = value[2:-1]
    if user_id == None:
        guild = bot.get_guild(SERVER_ID)
        for member in guild.members:
            if (
                member.nick is not None and member.nick == value
            ) or member.name == value:
                user_id = member.id

    return user_id


# Finds all proper requests, and sends a combined list of them all
@bot.slash_command(
    description="Get all requests.", guild_ids=[SERVER_ID], default_member_permissions=8
)
async def get_requests(interaction: nextcord.Interaction):
    combined_requests = {}
    await interaction.response.defer(ephemeral=True, with_message=True)

    for channel in interaction.guild.channels:
        if channel.id in request_channels:
            city_name = channel.name[2:-12]

            # Create a dictionary to store requests by station type
            station_requests = {}

            for thread in channel.threads:
                if thread.name.startswith("?"):
                    messages = await thread.history(
                        limit=15, oldest_first=True
                    ).flatten()
                    for message in messages:
                        if message.content.startswith("**"):
                            fetch_stations = False
                            for line in message.content.split("\n"):
                                if line.startswith("**Name:**"):
                                    _name = line[10:-1]
                                if fetch_stations:
                                    _station_name = line[2:]
                                    if _station_name not in station_requests:
                                        station_requests[_station_name] = {
                                            "solo": [],
                                            "guild": [],
                                            "alliance": [],
                                        }
                                    # Determine request type based on thread name
                                    if _request_type == "solo":
                                        station_requests[_station_name]["solo"].append(
                                            _name
                                        )
                                    elif _request_type == "guild":
                                        station_requests[_station_name]["guild"].append(
                                            _name
                                        )
                                    elif _request_type == "alliance":
                                        station_requests[_station_name][
                                            "alliance"
                                        ].append(_name)
                                if line.startswith("**Request type:**"):
                                    _request_type = line[18:]
                                if line.startswith("**Stations:**"):
                                    fetch_stations = True

                    # Organize the requests for each station type in a combined_data dictionary
                    combined_data = station_requests

                    # Add combined_data to the overall combined_requests
                    combined_requests[city_name] = combined_data

    try:
        await send_dm(interaction.user, combined_requests)
        await interaction.followup.send("Done! Check your dm's", ephemeral=True, delete_after=15)
    except:
        await interaction.followup.send(f"{interaction.user.name} has DM's disabled", ephemeral=True, delete_after=15)


async def send_dm(user, combined_requests):
    dm = await user.create_dm()

    # Get the current date and format it
    current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Create the initial message
    initial_message = f"Hello {user.mention}, here is your summary of requests as of {current_date}:\n\n"

    await dm.send(initial_message)

    for city, city_data in combined_requests.items():
        message = f"**{city}**"

        for station, station_data in city_data.items():
            message += f"\n**{station}\n**"

            # Check if there are any requests for each request type
            if station_data["solo"]:
                message += "Solo requests:\n"
                for request in station_data["solo"]:
                    message += f"- {request}\n"

            if station_data["guild"]:
                message += "Guild requests:\n"
                for request in station_data["guild"]:
                    message += f"- {request}\n"

            if station_data["alliance"]:
                message += "Alliance requests:\n"
                for request in station_data["alliance"]:
                    message += f"- {request}\n"

        # Send the message in chunks if it exceeds the 2000 characters limit
        while message:
            chunk, message = message[:2000], message[2000:]
            await send_chunk(user, chunk)



async def send_chunk(user, chunk):
    dm = await user.create_dm()
    await dm.send(chunk)


@bot.slash_command(
    description="Sends a message to every autorequest channel.",
    guild_ids=[SERVER_ID],
    default_member_permissions=8,
)
async def send_to_all(
    interaction: nextcord.Interaction,
    delete: bool = SlashOption(
        name="delete",
        description="Clear the channel from all existing messages.",
        required=True,  # Make delete option required
    ),
    message: str = SlashOption(
        name="message",
        description="Message to send to autorequest channels.",
        required=True,  # Make message option required
    ),
):
    # Get the guild
    await interaction.response.defer(ephemeral=True, with_message=True)
    guild = interaction.guild

    for channel_id in request_channels:
        channel = guild.get_channel(channel_id)
        if channel:
            if delete:
                await clear_channel(channel)
            await channel.send(message)
    await interaction.followup.send("Done!", ephemeral=True, delete_after=5)


async def clear_channel(channel):
    # Fetch and delete messages in the channel
    async for message in channel.history(limit=100):
        await message.delete()


@bot.slash_command(
    description="Shows information about stations in selected city.",
    guild_ids=[SERVER_ID],
    default_member_permissions=8,
)
async def display_stations(
    interaction: nextcord.Interaction,
    city: str = SlashOption(
        name="city",
        description="Choose city to display.",
        choices={
            "Fort Sterling": "fortsterling",
            "Lymhurst": "lymhurst",
            "Bridgewatch": "bridgewatch",
            "Martlock": "martlock",
            "Thetford": "thetford",
            "Caerleon": "caerleon",
            "All": "all",
        },
    ),
):
    guild = interaction.guild
    print(
        f"{interaction.user} has used display_stations in {interaction.channel} at {curr_time()} UTC"
    )
    await interaction.response.defer(ephemeral=True, with_message=True)


    if city == "all":
        # If "All" is selected, send to all request channels
        for channel_id in request_channels:
            channel = guild.get_channel(channel_id)
            if channel:
                await send_city_information(channel, guild, channel.name[2:-12])
    else:
        # Check if the city is in the predefined options
        if city in stations_images and city in stations.keys():
            channel = interaction.channel
            await send_city_information(channel, guild, city)
    await interaction.followup.send(f"Done!", ephemeral=True, delete_after=5)

async def send_city_information(channel, guild, city):
    if city in stations_images and city in stations.keys():
        image = stations_images[city][0]
        description = f"**Available shops in {city.title()}**"

        # Create owners and co-owners string to display in embed
        for station, owners in stations[city].items():
            description += f"\n**{station.title()}**"
            for owner in owners:
                description += f"\nOwner - <@{owner}>"
                if owner in stations_coowners:
                    description += f" Co-owners - "
                    for coowner in stations_coowners[owner]:
                        description += f"<@{coowner}> "

        # Embed creation
        description += (
            f"\n\nPlease use /request for requesting\n*Updated at {curr_time()} UTC*\n"
        )
        embedColor = _set_embed_colour(city)
        em = nextcord.Embed(description=description, color=embedColor)
        if city in stations_images:
            em.set_image(stations_images[city.lower()][0] + ".jpg")
        em.set_footer(text=f"Updated at {curr_time()} UTC\n")
        await channel.send(embed=em)
    elif city not in stations:
        embedColor = _set_embed_colour(city)
        description = f"We currently don't own any shops in {city.title()}, please wait for the next cycle."
        em = nextcord.Embed(description=description, color=embedColor)
        em.set_image(
            "https://thumbs.dreamstime.com/b/please-wait-test-clock-middle-delay-48693489.jpg"
        )
        em.set_footer(
            text=f"Updated at {curr_time()} UTC\n",
        )
        await channel.send(embed=em)
        await channel.send(
            f"{city} doesn't have any shops set. If that isn't intended, please set shops for the city and try again. If the problem keeps appearing, please contact <@158643072886898688>"
        )


# Displays all stations owned by provided owner
@bot.slash_command(
    description="Displays all stations from given owner.",
    guild_ids=[SERVER_ID],
    default_member_permissions=8,
)
async def owner_stations(
    interaction: nextcord.Interaction,
    owner: Optional[str] = SlashOption(
        description="Ping the owner or write his server name, if empty will display your stations"
    ),
):
    print(
        f"{interaction.user} has used owner_stations in {interaction.channel} at {curr_time()} UTC\n"
    )

    owner_id = _get_user_id(owner or interaction.user.name)
    description = ""
    for city in stations:
        for station in stations[city]:
            for owner in stations[city][station]:
                if str(owner_id) == str(owner):
                    if description == "":
                        description = f"**Displaying stations for <@{owner_id}>:**"
                    if city.title() not in description:
                        description += f"\n**{city.title()}: **"
                    description += f"{station.title()}, "
        if description[-2:] == ", ":
            description = description[:-2]

    if description != "":
        if int(owner_id) in stations_coowners:
            description += f"\n**Co-owners - **"
            for coowner in stations_coowners[int(owner_id)]:
                description += f"<@{coowner}> "

    if description == "":
        description = f"**<@{owner_id}> has no stations.**"
        if int(owner_id) in stations_coowners:
            description += f"\n**<@{owner_id}> has co-owners - **"
            for coowner in stations_coowners[int(owner_id)]:
                description += f"<@{coowner}> "

    await interaction.response.send_message(description, ephemeral=True)


# Adds co-owner to all stations of interaction.user
@bot.slash_command(
    description="Assigns co-owner to owner.",
    guild_ids=[SERVER_ID],
    default_member_permissions=8,
)
async def add_coowner(
    interaction: nextcord.Interaction,
    coowner: str = SlashOption(
        name="coowner", description="Ping the co-owner or write his server name."
    ),
    owner: Optional[str] = SlashOption(
        name="owner",
        description="Ping the owner or write his server name. If empty defaults to you.",
    ),
):
    print(
        f"{interaction.user} has used add_coowner in {interaction.channel} at {curr_time()} UTC\n"
    )

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
                    await interaction.followup.send(
                        f"<@{coowner_id}> is already co-owner of <@{owner_id}>'s stations.",
                        ephemeral=True,
                        delete_after=30,
                    )
                    return

                else:
                    stations_coowners[int(owner_id)].append(coowner_id)
                    database.insert_data(
                        "stations_coowners", owner_id=owner_id, coowner_id=coowner_id
                    )
                    await interaction.followup.send(
                        f"<@{coowner_id}> is now co-owner of <@{owner_id}>'s stations.",
                        ephemeral=True,
                        delete_after=30,
                    )
                    _update_stations_coowners()
                    return

    if owner_id not in stations_coowners:
        stations_coowners[owner_id] = [coowner_id]
        database.insert_data(
            "stations_coowners", owner_id=owner_id, coowner_id=coowner_id
        )
        await interaction.followup.send(
            f"<@{coowner_id}> is now co-owner of <@{owner_id}>'s stations.",
            ephemeral=True,
            delete_after=30,
        )
        _update_stations_coowners()
        return


# Removes given co-owner from interaction.user's stations
@bot.slash_command(
    description="Removes co-owner from owner.",
    guild_ids=[SERVER_ID],
    default_member_permissions=8,
)
async def remove_coowner(
    interaction: nextcord.Interaction,
    coowner: str = SlashOption(
        name="coowner", description="Ping the co-owner or write his server name."
    ),
    owner: Optional[str] = SlashOption(
        name="owner",
        description="Ping the owner or write his server name. If empty defaults to you.",
    ),
):
    print(
        f"{interaction.user} has used remove_coowner in {interaction.channel} at {curr_time()} UTC\n"
    )
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
                            "stations_coowners",
                            where=f"WHERE owner_id = {owner_id} and coowner_id = {coowner_id}",
                        )
                        _update_stations_coowners()
                        await interaction.followup.send(
                            f"<@{coowner_id}> is no longer co-owner of your stations.",
                            ephemeral=True,
                            delete_after=30,
                        )
                        return
                    except:
                        await interaction.followup.send(
                            f"Something went wrong. Please check if you wrote the command correctly and try again. If problem keeps occuring please contact <@158643072886898688>",
                            ephemeral=True,
                            delete_after=30,
                        )
    await interaction.followup.send(
        f"Couldn't find <@{owner_id}> - <@{coowner_id}> combination. \nCheck for typos, or try checking coowners_list with /owner_stations or /display_stations",
        ephemeral=True,
        delete_after=30,
    )


@bot.slash_command(
    description="Adds stations to the stations list.",
    guild_ids=[SERVER_ID],
    default_member_permissions=8,
)
async def add_stations(
    interaction: nextcord.Interaction,
    city: str = SlashOption(
        name="city",
        description="Chosen city",
        choices={
            "Fort Sterling": "fortsterling",
            "Lymhurst": "lymhurst",
            "Bridgewatch": "bridgewatch",
            "Martlock": "martlock",
            "Thetford": "thetford",
            "Caerleon": "caerleon",
        },
    ),
    stations: str = SlashOption(
        name="stations",
        description='Write stations you want to add in this format "hunter, warrior, mage..."',
    ),
    owner: Optional[str] = SlashOption(
        description="Ping the owner or write their server name. If empty, will add to your stations"
    ),
):
    print(
        f"{interaction.user} has used add_station in {interaction.channel} at "
        f"{curr_time()} UTC\n"
    )

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

        elif (city, station, owner_id) not in database.get_data(
            "stations", columns="DISTINCT city, station_name, owner_id"
        ):
            database.insert_data(
                "stations", city=city, station_name=station, owner_id=owner_id
            )

            if message == "":
                message += f"**Adding stations to <@{owner_id}> in {city.title()}: **\n"

            message += f"• {station.title()}\n"

        else:
            message += f"• {station.title()} is already added.\n"

    message += invalid_message

    if message != "":
        _update_stations_list()
        await interaction.followup.send(message, ephemeral=True, delete_after=30)

    else:
        await interaction.followup.send(
            "Did not add any stations.", ephemeral=True, delete_after=30
        )


# Deletes chosen station in city from selected owner. If no owner provided defaults to interaction.user
@bot.slash_command(
    description="Deletes stations from owner.",
    guild_ids=[SERVER_ID],
    default_member_permissions=8,
)
async def remove_stations(
    interaction: nextcord.Interaction,
    city: str = SlashOption(
        name="city",
        description="Chosen city",
        choices={
            "Fort Sterling": "fortsterling",
            "Lymhurst": "lymhurst",
            "Bridgewatch": "bridgewatch",
            "Martlock": "martlock",
            "Thetford": "thetford",
            "Caerleon": "caerleon",
        },
    ),
    stations: str = SlashOption(
        name="station",
        description='Chosen stations. Write in this format "hunter, warrior, mage..."',
    ),
    owner: Optional[str] = SlashOption(
        description="Ping the owner or write down his server name, if empty will remove your stations."
    ),
):
    print(
        f"{interaction.user} has used remove_stations in {interaction.channel} at {curr_time()} UTC\n"
    )
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
    db_stations = database.get_data(
        "stations", columns="DISTINCT city, station_name, owner_id"
    )
    for station in station_list:
        if station not in valid_stations:
            if invalid_message == "":
                invalid_message += "**Couldn't remove following stations: **"
            invalid_message += f"\n{station}"

        elif (str(city), str(station), int(owner_id)) in db_stations:
            database.delete_data(
                "stations",
                where=f'WHERE city = "{city}" AND station_name = "{station}" and owner_id = {owner_id}',
            )

            removed_message += f"• {station.title()}\n"

        else:
            message += f"• {station.title()} owned by <@{owner_id}> in {city.title()} not found in database.\n"
    if removed_message != "":
        message += f"**Removed stations from <@{owner_id}> in {city.title()}: **\n"
        message += removed_message
    message += invalid_message

    if message != "":
        _update_stations_list()
        await interaction.followup.send(message, ephemeral=True, delete_after=30)


# Sets stations image to given city. Needs URL to IMAGE to display properly.
@bot.slash_command(
    description="Sets the image of specified city.",
    guild_ids=[SERVER_ID],
    default_member_permissions=8,
)
async def set_image(
    interaction: nextcord.Interaction,
    city: str = SlashOption(
        name="city",
        description="Chosen city",
        choices={
            "Fort Sterling": "fortsterling",
            "Lymhurst": "lymhurst",
            "Bridgewatch": "bridgewatch",
            "Martlock": "martlock",
            "Thetford": "thetford",
            "Caerleon": "caerleon",
        },
    ),
    image: str = SlashOption(
        description="Image to display. Needs to be URL to an IMAGE."
    ),
):
    print(
        f"{interaction.user} has used set_image in {interaction.channel} at {curr_time()} UTC\n"
    )
    if city.lower() in stations_images.keys():
        database.delete_data("images", where=f'WHERE city = "{city.lower()}"')

    database.insert_data("images", city=city.lower(), image_link=image)
    _update_stations_images()
    await interaction.response.send_message(
        f"Image for {city} updated succesfully", ephemeral=True, delete_after=30
    )


# Deletes given amount of messages from interaction.channel
@bot.slash_command(
    description="Bulk deletes messages from current channel.",
    guild_ids=[SERVER_ID],
    default_member_permissions=8,
)
async def delete_messages(
    interaction: nextcord.Interaction,
    amount: int = SlashOption(description="Amount of messages to delete."),
):
    print(
        f"{interaction.user} has used delete_messages in {interaction.channel} at {curr_time()} UTC\n"
    )
    if amount > 100:
        await interaction.response.send_message(
            f"Amount needs to be less than 100.", ephemeral=True, delete_after=5
        )
    else:
        await interaction.response.send_message(
            f"Deleting {amount} messages.", ephemeral=True, delete_after=5
        )
        await interaction.channel.purge(limit=amount)


# TDeveloping test command
@bot.slash_command(
    description="Command for testing. Don't use it. Can do nothing, or can break everything.",
    guild_ids=[SERVER_ID],
    default_member_permissions=8,
)
async def test_command(interaction: nextcord.Interaction):
    print(stations)


if __name__ == "__main__":
    database.connect("stations.db")
    database.create_table(
        "stations_coowners", [("owner_id", "INTEGER"), ("coowner_id", "INTEGER")]
    )
    database.create_table(
        "stations",
        [("city", "TEXT"), ("station_name", "TEXT"), ("owner_id", "INTEGER")],
    )
    database.create_table("images", [("city", "TEXT UNIQUE"), ("image_link", "TEXT")])
    database.create_table(
        "muted",
        [("user_id", "TEXT"), ("date", "TEXT"), ("reason", "TEXT"), ("length", "TEXT")],
    )

    taskCog = TaskCog(bot)
    buttonCog = ButtonCog(bot)
    mutedCog = MutedCog(bot)

    bot.add_cog(buttonCog)
    bot.add_cog(taskCog)
    bot.add_cog(mutedCog)

    bot.run(TOKEN)
