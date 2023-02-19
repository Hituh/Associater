"""try: from .player_scrapper import *
except:from player_scrapper import *

try: from .id_scrapper import id_scrapper
except: from id_scrapper import id_scrapper

from mylibs.geral.datestring import *
import requests
import json
import pandas as pd

class Guild:

    def __init__(self, name, **kargs):
        self.base_url = 'https://gameinfo.albiononline.com/api/gameinfo/guilds/'
        
        if isinstance(name, str):
            self.name = name.lower()
        else:
            self.name = name[0].lower()
            self.id = name[1]

        self.fame_history = []
        self.members = []
        if kargs:
            self.id = kargs['Id']
            #self.fame_history.append([kargs['Fame'], datestring(string='%Y%m%d')])
        else:
            pass


    def update(self):
        try:
            if self.id:
                pass
            else:
                print('I think the guild wasnt found. Please check the name again please')
                return False
        except:
            _id = id_scrapper(self.name, _type='guilds')
            if not _id:
                print('I think the guild wasnt found. Please check the name again please')
                return False
            else:
                self.id = _id['Id']
        
        while 1:
            try:
                self.data = requests.get(self.base_url+self.id).json()
                self.data_members = requests.get(self.base_url+self.id+'/members').json()
            
            except:
                print('Request guild data timed out. Trying again in 10 seconds')
                sleep(10)
                continue
            break
        

        return True


    def get_members(self, sort_by='Name', descending=False):
        '''sort_by keys: Name, Fame, Fame_previous_week'''


        print('Requesting members list for guild {} ({}).'.format(self.name, self.id))

        members = []
        for member in self.data_members:
            pass
            members.append(Player(name=member['Name'], Id=member['Id'], Fame=int(member['LifetimeStatistics']['Crafting']['Total']), GuildName=self.name, GuildId=self.id, data=member))

        print('Member list adquired.\n')
        
        #sort_keys = {'Name': members.name, 'Fame': members.get_fame(), 'Fame_previous_week': members.fame_previous_week()}
        
        if sort_by == 'Fame':
            members.sort(key = lambda members: members.get_fame(), reverse=descending)
        elif sort_by == 'Fame_previous_week':
            members.sort(key = lambda members: members.fame_previous_week(), reverse=descending)
        else:
            members.sort(key = lambda members: members.name, reverse=descending)
        
        return members


    def update_members(self):
        if self.update():
            self.last_state = self.members
            self.members = self.get_members()
        else:
            print('Something failed during the update_members routine')


    def update_alliance(self):
        self.update()
        self.alliance_id = self.data['AllianceId']
        if self.alliance_id != '':
            try:
                alliance = requests.get('https://gameinfo.albiononline.com/api/gameinfo/alliances/'+self.alliance_id).json()
                self.alliance_name = alliance['AllianceName'].lower()
                self.alliance_tag = alliance['AllianceTag']
            except:
                print('Couldnt adquire alliance. Please consider trying again later.')
                self.alliance_name = None
                self.alliance_tag = None
        else:
            self.alliance_name = None
            self.alliance_tag = None
            self.alliance_id = None


    def as_string(self, quantity=False, sort_by = 'Fame_previous_week', descending=True):
        '''sort_by keys: Name, Fame, Fame_previous_week'''
        sort_keys = {'Name': 'Member', 'Fame': 'Crafting Fame', 'Fame_previous_week': 'Fame previous week'}
        
        if self.alliance_id != '':
            alliance = 'is part of the alliance [{}] ({}).'.format(self.alliance_tag, self.alliance_name)
        else:
            alliance = 'isnt part of an alliance afaik.'
        return_msg = 'The guild [{}] {}\nCurrently the guild has {} members.\n'.format(self.name, alliance, len(self.members))

        if not quantity:
            quantity = len(self.members)
            return_msg += 'The member list is:\n'
        else:
            return_msg += 'The first {} members ordered by {} are:\n'.format(quantity, sort_keys[sort_by])
        #if quantity:
        #    members =  self.members[:quantity]
        #else:
        #    members = self.members
        
        
        

        members = [{'Member': member.name, 'Crafting Fame': member.get_fame(), 'Fame previous week': member.fame_previous_week()} for member in self.members]

        members = sorted(members, key=lambda member: member[sort_keys[sort_by]], reverse=descending)
        df = pd.DataFrame(members[:quantity])
        df.index+=1
        try:
            df['Crafting Fame'] = df['Crafting Fame'].apply(lambda x : '{val:,}'.format(val=x))
            df['Fame previous week'] = df['Fame previous week'].apply(lambda x : '{val:,}'.format(val=x))
        except:
            print('An exception was raised during the processing of the dataframe Fame values')
        
        return_msg += df.to_string()
        return return_msg
        
        #return '\n'.join(['[{}] {<}'.format(index+1, member)




def main():

    current_associates_list = '{ "@_Owner" : "owner", "@_Guild" : "friend", "@_Everyone" : "user", "Player:UTFTitus" : "friend", "Alliance:Big Crafters work Hard" : "friend", "Alliance:Partnership of Equals" : "friend", "Alliance:EQMS Praise Be Archersnon" : "friend", "Alliance:ARCH BR" : "friend", "Alliance:Awful Company Hispano" : "friend", "Player:Hunter01" : "coowner", "Alliance:RIP POP" : "friend", "Alliance:Ride the Wave or Drown" : "friend", "Guild:We Craft" : "friend", "Alliance:Partnership Of Brazilians" : "friend", "Guild:Fart guild" : "friend", "Alliance:PARENTAL CONTROL" : "friend", "Alliance:Resurgence 2" : "friend", "Player:Mcaisz" : "friend", "Alliance:Stand By You" : "friend", "Alliance:Howl of war" : "friend", "Guild:Fawars" : "friend", "Alliance:Regear Come Back" : "friend", "Guild:3mpire" : "friend", "Guild:0 R I G E N" : "friend", "Guild:BKO" : "friend", "Guild:Guildzinha" : "friend", "Alliance:Log Out 4 CTA" : "friend", "Player:01HOmelet" : "friend", "Alliance:All Brazilians Reunited" : "friend", "Alliance:Super odd rabbits racking you" : "friend", "Guild:FA5ON47" : "friend", "Guild:MudHouse" : "friend" }'
    current_associates_list = json.loads(current_associates_list)

    guilds_list = [associate[6:] for associate in current_associates_list.keys() if associate[:5] == 'Guild']
    print('The current guilds in the associates list are:', ', '.join(guilds_list),'\n')


    guilds_list = guilds_list[:4]
    guilds_list = ['Murder crafters', ]
    for g in guilds_list:

        guild = Guild(g)
        guild.update_members()

        print(guild.as_string())
        print('-'*60)

def main2():
    guild = Guild('Full Reapers')
    guild.update()
    guild.update_members()
    guild.update_alliance()


    #print(guild.get_members())
    print(guild.as_string(quantity=10, sort_by='Fame'))

def main3():
    _id = id_scrapper('Hunter01')
    print(_id)

def main4(ctx, name: str = None, *stations):

    if name[0] != '(':
        message = 'Hi, you did send ({}) to me but I couldnt understand. Did you put the name between ( )?.\nPlease try again.'.format(1)
        print(message)
        return
    elif name[-1] != ')':
        checked = []
        stations = list(stations)
        for station in stations:
            if station[-1] == ')':
                name = ' '.join([name[1:], *checked, station[:-1]])
                checked.append(station)
                for check in checked:
                    stations.pop(0)
                break
            else:
                checked.append(station)


        else:
            message = 'Hi, you did send ({}) to me but I couldnt understand. Did you put the name between ( )?.\nPlease try again.'.format(1)
            print(message)
            return

    print(name)
    print(stations)

def main5():
    pass

if __name__ == '__main__':
    main3()"""