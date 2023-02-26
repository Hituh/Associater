# from .player_scrapper import *
# from .guild_scrapper import *
# from .station_entries import station_entries
# import json
# import threading

# #class station_entries was here

# def find_duplicate(associate_list):

#     associate_list = station_entries(associate_list)

#     #print('Players:', associate_list.players)
#     #print('\nGuilds:', associate_list.guilds)
#     #print('\nAlliances:', associate_list.alliances)

#     associate_list_dict = {
#         'alliances': [associate.lower() for associate in associate_list.alliances],
#         'guilds': [associate.lower() for associate in associate_list.guilds],
#         'players': [associate.lower() for associate in associate_list.players]}
    
#     entries = {'alliances': [], 'guilds': [], 'players': []}

#     threads = []

#     def check_player():
#         p = associate_list.players.pop()
#         entry = Player(p)
#         entry.update()
#         #associate_list_dict['players'].append(entry)
#         entries['players'].append(entry)

#     def check_guild():
#         g = associate_list.guilds.pop()
#         entry = Guild(g)
#         entry.update()
#         entries['guilds'].append(entry)


#     for p in associate_list.players[:]:
#         t = threading.Thread(target=lambda : check_player())
#         t.daemon=True
#         threads.append(t)


#     for g in associate_list.guilds[:]:
#         t = threading.Thread(target=lambda : check_guild())
#         t.daemon=True
#         threads.append(t)

#     for a in associate_list.alliances:
#         entries['alliances'].append(a)


#     for i in range(len(threads)):
#         threads[i].start()
    
#     for i in range(len(threads)):
#         threads[i].join()


#     guildless_players = []
#     one_player_guilds = []
#     player_in_guild = []
#     player_in_guild_alliance_less = []
#     player_in_alliance = []
#     players_in_same_guild = []
#     players_in_same_alliance = []


#     alliance_less_guilds = []
#     one_guild_alliances = []
#     guild_in_alliance = []
#     guilds_in_same_alliance = []


#     for p in entries['players']:
#         pass
#         if p.guild_name == None:
#             guildless_players.append(p)
#             #continue

#         else:
#             if p.guild_members_count == 1:
#                 one_player_guilds.append(p)

#             if p.guild_name.lower() in associate_list_dict['guilds']:
#                 player_in_guild.append(p)
            
#             if p.alliance_name == None:
#                 player_in_guild_alliance_less.append(p)
            
#             elif p.alliance_name.lower() in associate_list_dict['alliances']:
#                 player_in_alliance.append(p)

#         for _p in entries['players']:
#             if (p != _p):
#                 if (p.guild_name != None and _p.guild_name != None) and (p.guild_name == _p.guild_name):
#                     players_in_same_guild.append(p)
#                 if (p.alliance_name != None and _p.alliance_name != None) and (p.alliance_name == _p.alliance_name):
#                     players_in_same_alliance.append(p)

#     for g in entries['guilds']:
#         if g.alliance_name == None:
#             alliance_less_guilds.append(g)
        
#         else:
#             if g.alliance_guilds_count == 1:
#                 one_guild_alliances.append(g)

#             if g.alliance_name.lower() in associate_list_dict['alliances']:
#                 guild_in_alliance.append(g)


#         for _g in entries['guilds']:
#             if (g != _g):
#                 if (g.alliance_name != None and _g.alliance_name != None) and (g.alliance_name == _g.alliance_name):
#                     guilds_in_same_alliance.append(g)

#     #print(f'Players: {associate_list_dict["players"]}')
#     #print(f'Guilds: {associate_list_dict["guilds"]}')
#     #print(f'Alliances: {associate_list_dict["alliances"]}')


#     duplicate_msg = '-'*30


#     for alliance_name, alliance_tag in list(set([(_g.alliance_name, _g.alliance_tag) for _g in guilds_in_same_alliance])):
#         duplicate_msg += f'\n\nThe following Guilds are in the same Alliance: [{alliance_tag}] {alliance_name}\n'
#         for _g in [_g for _g in guilds_in_same_alliance if _g.alliance_name.lower() == alliance_name.lower()]:
#             duplicate_msg += f'({_g.name}) ({_g.members_count} members)\n'

#     for alliance_name, alliance_tag in list(set([(_g.alliance_name, _g.alliance_tag) for _g in guild_in_alliance])):
#         duplicate_msg += f'\n\nThe following Guilds are in the Alliance: [{alliance_tag}] {alliance_name} (Which is also in the list)\n'
#         for _g in [_g for _g in guild_in_alliance if _g.alliance_name.lower() == alliance_name.lower()]:
#             duplicate_msg += f'[{_g.name}] ({_g.members_count} members)\n'

#     if one_guild_alliances:
#         duplicate_msg += '\n\n'
#         for _g in one_guild_alliances:
#             duplicate_msg += f'The Guild ({_g.name}) ({_g.members_count} members) is alone in the Alliance [{_g.alliance_tag}] ({_g.alliance_name}).\n'

#     if alliance_less_guilds:
#         duplicate_msg += '\n\n'
#         for _g in alliance_less_guilds:
#             duplicate_msg += f'The Guild ({_g.name}) ({_g.members_count} members) is Alliance-less.\n'

#     #------------------------
#     duplicate_msg += '\n' + '-'*30

#     for alliance_name, alliance_tag in list(set([(_p.alliance_name, _p.alliance_tag) for _p in players_in_same_alliance])):
#         duplicate_msg += f'\n\nThe following Players are in the same alliance: [{alliance_tag}] {alliance_name}\n'
#         for _p in [_p for _p in players_in_same_alliance if _p.alliance_name.lower() == alliance_name.lower()]:
#             duplicate_msg += f'{_p.name} (Guild: {_p.guild_name})\n'

#     for guild_name in list(set([_p.guild_name for _p in players_in_same_guild])):
#         duplicate_msg += f'\n\nThe following Players are in the same Guild: ({guild_name})\n'
#         for _p in [_p for _p in players_in_same_guild if _p.guild_name.lower() == guild_name.lower()]:
#             duplicate_msg += f'{_p.name}\n'

#     for alliance_name, alliance_tag in list(set([(_p.alliance_name, _p.alliance_tag) for _p in player_in_alliance])):
#         duplicate_msg += f'\n\nThe following Players are in the Alliance: [{alliance_tag}] {alliance_name} (Which is also in the list)\n'
#         for _p in [_p for _p in player_in_alliance if _p.alliance_name.lower() == alliance_name.lower()]:
#             duplicate_msg += f'{_p.name}\n'

#     #player_in_guild_alliance_less = []

#     for guild_name in list(set([_p.guild_name for _p in player_in_guild])):
#         duplicate_msg += f'\n\nThe following Players are in the Guild: {guild_name} (Which is also in the list)\n'
#         for _p in [_p for _p in player_in_guild if _p.guild_name.lower() == guild_name.lower()]:
#             duplicate_msg += f'{_p.name}\n'

#     if one_player_guilds:
#         duplicate_msg += '\n\n'
#         for _p in one_player_guilds:
#             duplicate_msg += f'The Player ({_p.name}) is alone in the Guild ({_p.guild_name}).\n'

#     if guildless_players:
#         duplicate_msg += '\n\n'
#         for _p in guildless_players:
#             duplicate_msg += f'The Player ({_p.name}) is Guild-less.\n'


#     return duplicate_msg




# if __name__ == '__main__':
#     pass