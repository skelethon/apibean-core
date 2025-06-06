import json

def print_json(data, indent:int=2):
    print(json.dumps(data, ensure_ascii=False, indent=indent))

def pretty_print_json(*args, **kwargs):
    return print_json(*args, **kwargs)
