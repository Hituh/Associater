import sqlite3

class Database:
    def __init__(self, db_file, check_same_thread = True):
        self.conn = sqlite3.connect(db_file, check_same_thread=check_same_thread)
        self.c = conn.cursor()


#Database('associates_manager_database.db')


conn = None
c = None

def connect(database_file, check_same_thread = True):
    global conn, c
    conn = sqlite3.connect(database_file, check_same_thread = check_same_thread)
    c = conn.cursor()


def table_exists(table_name): 
    c.execute('''SELECT count(name) FROM sqlite_master WHERE TYPE = 'table' AND name = '{}' '''.format(table_name)) 
    if c.fetchone()[0] == 1: 
        return True 
    return False


def create_table(table_name, columns):
    '''
    columns is a list of (column_name, TYPE)
    '''
    if not table_exists(table_name):
        columns = ', '.join(['"{}" {}'.format(column[0], column[1]) for column in columns])
        
        statement = '''CREATE TABLE {}({})'''.format(table_name, columns)
        c.execute(statement)
    else:
        print(f'Table [{table_name}] already exist.')


def insert_data(table_name, **kargs):
    n = ', '.join(['?']*len(kargs))
    keys = ', '.join([str(key) for key in kargs.keys()])
    
    command = ''' INSERT INTO {} ({}) VALUES({}) '''.format(table_name, keys, n)
    #print(command, tuple(kargs.values()))

    c.execute(command, tuple(kargs.values()))
    conn.commit()
    return True


def update_data(table_name, replacement, where, aditional_arg = ''):
    try:
        command = f'''UPDATE {table_name} SET {replacement} {where} {aditional_arg}'''

        c.execute(command)
        conn.commit()
        return True
    except:
        print(f'Error while calling the querry ({command})')
        return False


def delete_data(table_name, where, aditional_arg=''):
    try:
        command = f'''DELETE FROM {table_name} {where} {aditional_arg}'''
    
        c.execute(command)
        conn.commit()
        return True
    except:
        return False


def get_data(table_name, columns='*', where= '', order_by='', n:int=False):
    command = f'''SELECT {columns} FROM {table_name} {where} {order_by}'''
    #print(command)
    c.execute(command)

    if not n:
        return c.fetchall()
    else:
        return c.fetchmany(n)




