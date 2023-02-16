import json

def read_datasource_config(file_path: str) -> list:
    with open(file_path, 'r') as f:
        data = json.load(f)

    return data
