# try: from ..scrapper.id_scrapper import id_scrapper
# except: from id_scrapper import id_scrapper

# try: from .player_scrapper import Player
# except: from player_scrapper import Player


# from aux_libraries.datestring import *
# import requests
# #import json
# #import pandas as pd
# from time import sleep

# class Guild:

#     def __init__(self, name, **kargs):
#         self.base_url = 'https://gameinfo.albiononline.com/api/gameinfo/guilds/'
        
#         if isinstance(name, str):
#             self.name = name.lower()
#         else:
#             self.name = name[0].lower()
#             self.id = name[1]


#         if kargs:
#             self.id = kargs['Id']
#         else:
#             pass


#     def update(self):
#         try:
#             if self.id:
#                 pass
#             else:
#                 print('I think the guild wasnt found. Please check the name again please')
#                 return False
#         except:
#             _id = id_scrapper(self.name, _type='guilds')[0]
#             if not _id:
#                 print('I think the guild wasnt found. Please check the name again please')
#                 return False
#             else:
#                 self.id = _id['Id']
        

#         max_tries = 6
#         status_code = 0
#         for _try in range(max_tries):
#             try:
#                 request = requests.get(self.base_url+self.id, timeout=60)
#                 status_code = request.status_code
#                 self.data = request.json()

#                 request = requests.get(self.base_url+self.id+'/members', timeout=60)
#                 status_code = request.status_code
#                 self.data_members = request.json()
#                 self.members_count = len(self.data_members)

#                 self.alliance_id = self.data['AllianceId']
#                 if self.alliance_id != '':
#                     request = requests.get('https://gameinfo.albiononline.com/api/gameinfo/alliances/'+self.alliance_id, timeout=60)
#                     status_code = request.status_code

#                 if (self.alliance_id != '') and ('Problem accessing /api/gameinfo/alliances/' not in str(request.text)):
#                     alliance = request.json()
#                     self.alliance_name = alliance['AllianceName']
#                     self.alliance_tag = alliance['AllianceTag']
#                     self.alliance_guilds_count = len(alliance['Guilds'])
#                     self.alliance_members_count = alliance['NumPlayers']
#                 else:
#                     self.alliance_id = None
#                     self.alliance_name = None
#                     self.alliance_tag = None
#                     self.alliance_guilds_count = 0
#                     self.alliance_members_count = 0


#                 break
#             except:
#                 print('Requested guild data timed out. Trying again in 10 seconds')
#                 sleep(10)
#         if ('Problem accessing /api/gameinfo/alliances/' in str(request.text)):
#             pass
#             print('Skipping aliance error on API request')
#         elif ('<head><title>404 Not Found</title></head>' in str(request.text)):
#             print(f'Skipping guild error on API request for guild id {self.id} and waiting 3600 seconds to try again')
#             sleep(3600)
#             return self.update()
#         elif (status_code != 200):
#             if (status_code != 0):
#                 print(request.status_code)
#                 print(request.text)
#             print('Something failed during the update. Trying again in 60 seconds.')
#             sleep(60)
#             return self.update()
#             #return False


#         return True


#     def get_members(self, sort_by='Name', descending=False):
#         '''sort_by keys: Name, Fame, Fame_previous_week'''


#         print('Requesting members list for guild {} ({}).'.format(self.name, self.id))

#         members = []
#         for member in self.data_members:
#             p = Player(name=member['Name'], Id=member['Id'], Fame=int(member['LifetimeStatistics']['Crafting']['Total']), GuildName=self.name, GuildId=self.id, alliance_name=member['AllianceName'], alliance_id = member['AllianceId'], alliance_tag = member['AllianceTag'], data=member)
#             members.append(p)

#         print('Member list adquired.\n')
        
#         #sort_keys = {'Name': members.name, 'Fame': members.get_fame(), 'Fame_previous_week': members.fame_previous_week()}
        
#         if sort_by == 'Fame':
#             members.sort(key = lambda members: members.get_fame(), reverse=descending)
#         elif sort_by == 'Fame_previous_week':
#             members.sort(key = lambda members: members.fame_previous_week(), reverse=descending)
#         else:
#             members.sort(key = lambda members: members.name, reverse=descending)

#         return members



# def main():
#     guilds_list = ['Murder crafters', ]
#     count = 0
#     chars = []
#     for g in guilds_list:

#         guild = Guild(g)
#         guild.update()
#         print(guild.name, guild.id, guild.alliance_tag, guild.alliance_name, guild.alliance_id, guild.members_count)
#         for m in guild.get_members():
#             #print('-'*60)
#             print([m.name, m.id, m.guild_name, m.guild_id, m.get_fame(), m.fame_previous_week()])



# def main2():
#     pass

#     _range = ['week', 'lastWeek', 'month', 'lastMonth']

#     _type = {'PvE':{'subtype': ['',], 'region': ['Total', 'Royal', 'Outlands', 'Hellgate', 'Avalon', 'CorruptedDungeon']}, 
#         'Crafting':{'subtype': ['',], 'region': ['Total', 'Royal', 'Outlands', 'Avalon',]},
#         'Gathering':{'subtype': [f'&subtype={s}' for s in ['Fiber', 'Hide', 'Ore', 'Rock', 'Wood']], 'region': ['Total', 'Royal', 'Outlands', 'Avalon',]}}

#     #_subtype = ['Fiber', 'Hide', 'Ore', 'Rock', 'Wood'] #All
#     #&subtype=All
#     #_region = ['Total', 'Royal', 'Outlands', 'Hellgate', 'Avalon', 'CorruptedDungeon']

#     _limit = 1000
#     _offset = 0

#     players = []
#     ids = []
#     count = 0

#     for r in _range:
#         for t in _type.keys():
#             for subtype in _type[t]['subtype']:
#                 for region in _type[t]['region']:
#                     request_url = f'https://gameinfo.albiononline.com/api/gameinfo/players/statistics?range={r}&limit={_limit}&offset={_offset}&type={t}{subtype}&region={region}'
#                     #print(request_url)
#                     request = requests.get(request_url).json()
#                     for response in request:
#                         player_name = response['Player']['Name']
#                         player_id = response['Player']['Id']

#                         if player_name not in players:
#                             players.append(player_name)
#                             ids.append(player_id)

#                             count+=1
#                             print(f'{count:05d}', player_id, player_name)
#                             sleep(0.1)


# if __name__ == '__main__':
#     pass
#     main()
