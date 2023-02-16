

import json
from pyfi_core.modules.views.transaction import RegexFieldFilterStrategy


def read_view_config(file_path):
    with open(file_path) as f:
        data = json.load(f)
    
    view_config = []
    
    for item in data:
        name = item['name']
        filters = {}
        for key, value in item['filters'].items():
            filter_strategies = []
            for filter_strategy in value:
                if filter_strategy['type'] == 'RegexFieldFilterStrategy':
                    filter_strategies.append(
                        RegexFieldFilterStrategy(
                            filter_strategy['field_name'], 
                            filter_strategy['regex']
                        )
                    )
            filters[key] = filter_strategies
        
        view_config.append({
            'name': name,
            'filters': filters
        })
    
    return view_config