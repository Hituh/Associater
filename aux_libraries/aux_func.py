def only_alnum(string: str):
    return ''.join([i if i.isalnum() else '' for i in string])
