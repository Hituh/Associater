import requests
#import json
from time import sleep

def id_scrapper(name, _type='any'):

    '''
    type may be 'players', 'guilds' or 'any'
    '''

    base_url = 'https://gameinfo.albiononline.com/api/gameinfo/search?q='

    max_tries = 6
    status_code = 0
    for _try in range(max_tries):
        try:
            request = requests.get(base_url+name, timeout=30)
            status_code = request.status_code
            break
        except:
            print('Request timed out. Trying again in 10 seconds')
            sleep(10)


    if (status_code != 200):
        if (status_code != 0):
            print(request.status_code)
            print(request.text)
        print('Something failed during the request. Trying again in 60 seconds.')
        sleep(60)
        #return False
        return id_scrapper(name=name, _type=_type)

    data = request.json()

    _types = data.keys() if _type == 'any' else [_type, ]
    found_matches = []
    for _type in list(_types)[::-1]:
        for entrance in data[_type]:
            if entrance['Name'].lower() == name.lower():
                print(f'Found. Name - {name} Type - {_type[:-1]}')
                found_matches.append(
                    {'Id': entrance['Id'], 'Type': _type[:-1]})

    if found_matches:
        return found_matches

    print('Looks like nothing was found on the search key. The result was like: status={} and the plain-text={}'.format(request.status_code, request.text))
    return False #Means the name wasnt found

#print(id_scrapper('Hunter01'))

