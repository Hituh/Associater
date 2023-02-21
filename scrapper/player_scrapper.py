try:
    from .id_scrapper import id_scrapper

except:
    from id_scrapper import id_scrapper


from aux_libraries.datestring import *
import requests
#import json
from time import sleep


class Player:
    def __init__(self, name, **kargs):
        self.base_url = 'https://gameinfo.albiononline.com/api/gameinfo/players/'

        if isinstance(name, str):
            self.name = name.lower()
        else:
            self.name = name[0].lower()
            self.id = name[1]

        ###self.fame_history = []

        if kargs:
            self.id = kargs['Id']
            ###self.fame_history.append([kargs['Fame'], datestring(string='%Y%m%d')])
            self.guild_name = kargs['GuildName'].lower()
            self.guild_id = kargs['GuildId']

            self.alliance_name = kargs['alliance_name']
            self.alliance_id = kargs['alliance_id']
            self.alliance_tag = kargs['alliance_tag']

            self.data = kargs['data']
        else:
            pass


    def update(self):
        try:
            if self.id:
                pass
            else:
                print('I think the player wasnt found. Please check nickname again please')
                return False
        except:
            _id = id_scrapper(self.name, _type='players')[0]
            if not _id:
                print('I think the player wasnt found. Please check nickname again please')
                return False
            else:
                self.id = _id['Id']


        max_tries = 6
        status_code = 0
        for _try in range(max_tries):
            try:
                request = requests.get(self.base_url+self.id, timeout=30)
                status_code = request.status_code
                self.data = request.json()

                if self.data['GuildId'] != '':
                    self.guild_id = self.data['GuildId']
                    self.guild_name = self.data['GuildName']

                    request = requests.get('https://gameinfo.albiononline.com/api/gameinfo/guilds/'+self.guild_id+'/members', timeout=60)
                    status_code = request.status_code
                    self.guild_members_count = len(request.json())
                else:
                    self.guild_id = None
                    self.guild_name = None
                    self.guild_members_count = 0
                

                if self.data['AllianceId'] != '' and (self.data['AllianceName'] == '' or self.data['AllianceTag'] == ''):
                    self.alliance_id = self.data['AllianceId']

                    request = requests.get('https://gameinfo.albiononline.com/api/gameinfo/alliances/'+self.alliance_id, timeout=60)
                    #print(self.alliance_id)
                    #print(request.text)
                    status_code = request.status_code
                    
                    alliance = request.json()
                    self.alliance_name = alliance['AllianceName']
                    self.alliance_tag = alliance['AllianceTag']
                    self.alliance_guilds_count = len(alliance['Guilds'])
                    self.alliance_members_count = alliance['NumPlayers']
                else:
                    self.alliance_id = None
                    self.alliance_name = None
                    self.alliance_tag = None
                    self.alliance_guilds_count = 0
                    self.alliance_members_count = 0

                break

            except:
                print('Player update timed out. Trying again in 10 seconds')
                sleep(10)
        if (status_code != 200):
            if (status_code != 0):
                print(request.status_code)
                print(request.text)
            print('Something failed during the update. Trying again in 60 seconds.')
            sleep(60)
            return self.update()
            #return False


        return True


    def get_fame(self):
        fame = self.data['LifetimeStatistics']['Crafting']['Total']
        return fame


    def fame_previous_week(self):
        if not self.guild_id:
            return False

        last_week_url = 'https://gameinfo.albiononline.com/api/gameinfo/players/statistics?range=lastWeek&limit=30&offset=0&type=Crafting&region=Total&guildId='

        max_tries = 6
        status_code = 0
        for _try in range(max_tries):
            try:
                request = requests.get(last_week_url+self.guild_id, timeout=30)
                status_code = request.status_code

                fame_previous_week = request.json()
                for p in fame_previous_week:
                    if p['Player']['Name'].lower() == self.name.lower():
                        return (p['Fame'])
                #print(f'Searched for {self.name} in the guild {self.guild} but couldnt find the fame in the previous week.')
                return 0#None
            except:
                sleep(10)
                return self.fame_previous_week()




def main():


    players_list = ['Hunter01', ]


    for p in players_list:
        player = Player(p)
        player.update()

        print([player.name, player.id, player.guild_name, player.guild_id, player.get_fame(), player.fame_previous_week()])
        print('-'*60)


if __name__ == '__main__':
    pass
    #main()

