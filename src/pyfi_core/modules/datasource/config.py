import json
from importlib import import_module

def read_file(json_file_path):
    with open(json_file_path, 'r') as json_file:
        data = json.load(json_file)
        return read_json(data)

def read_json(data):
    config = []
    for item in data:
        config.append({
            'name': item['name'],
            "datasource" : parse_datasource_definition(item['definition'])
        })
    return config

def parse_datasource_definition(definition):
    module_name, class_name = definition['type'].rsplit('.', 1)
    module = import_module(module_name)
    obj_type = getattr(module, class_name)
    datasource_instance = obj_type(definition['path'])
    return datasource_instance