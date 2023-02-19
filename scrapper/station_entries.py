import json

class station_entries:
    def __init__(self, _list):
        if type(_list) == str:
            self.list = json.loads(_list)
        else:
            self.list = _list

        self.players = [associate[7:] for associate in self.list.keys() if associate[:6] == 'Player']
        self.guilds = [associate[6:] for associate in self.list.keys() if associate[:5] == 'Guild']
        self.alliances = [associate[9:] for associate in self.list.keys() if associate[:8] == 'Alliance']

    def print_list(self):
        print_return = ''
        if self.players:
            print_return += 'Players:\n'
            for index, p in enumerate(self.players):
                print_return += '    {:02d} [{}]\n'.format(index+1, p)
            print_return += '\n'
        else:
            print_return += 'No players at the list.\n'
            print_return += '\n'
        
        if self.guilds:
            print_return += 'Guilds:\n'
            for index, p in enumerate(self.guilds):
                print_return += '    {:02d} [{}]\n'.format(index+1, p)
            print_return += '\n'
        else:
            print_return += 'No guilds at the list.\n'
            print_return += '\n'
        
        if self.alliances:
            print_return += 'Alliances:\n'
            for index, p in enumerate(self.alliances):
                print_return += '    {:02d} [{}]\n'.format(index+1, p)
            print_return += '\n'
        else:
            print_return += 'No Alliances at the list.\n'
            print_return += '\n'
        
        return print_return




def main():
    pass
    station = station_entries('{ "@_Owner" : "owner", "@_Guild" : "friend", "@_Everyone" : "user", "Alliance:Resurgence 2" : "friend", "Alliance:Big Crafters work Hard" : "friend", "Alliance:Partnership of Equals" : "friend", "Alliance:EQMS Praise Be Archersnon" : "friend", "Alliance:ARCH BR" : "friend", "Alliance:Awful Company Hispano" : "friend", "Player:Hunter01" : "coowner", "Alliance:RIP POP" : "friend", "Alliance:Ride the Wave or Drown" : "friend", "Guild:We Craft" : "friend", "Alliance:Partnership Of Brazilians" : "friend", "Alliance:Howl of war" : "friend", "Alliance:Stand By You" : "friend", "Guild:JustaCrafering" : "friend", "Guild:3mpire" : "friend", "Guild:Guildzinha" : "friend", "Guild:Real Bears" : "friend", "Alliance:Log Out 4 CTA" : "friend", "Alliance:All Brazilians Reunited" : "friend", "Guild:MudHouse" : "friend", "Player:Duderino123" : "friend", "Player:01HOmelet" : "coowner", "Guild:Scarlet Monastery" : "friend", "Player:Rud1" : "coowner" }')
    print(station.players)
    print(station.guilds)
    print(station.alliances)





if __name__ == '__main__':
    main()
