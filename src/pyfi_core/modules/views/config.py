

import json
import logging
import sys
from pyfi_core.modules.views.transaction import AmountFilterStrategy, RegexFieldFilterStrategy


def read_file(json_file_path):
    with open(json_file_path, 'r') as f:
        data = json.load(f)
        return read_json(data)

def read_json(data):
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
                if filter_strategy['type'] == 'AmountFilterStrategy':
                    min_value = float(filter_strategy['min_value']) if filter_strategy['min_value'] else -float(sys.maxsize)
                    max_value = float(filter_strategy['max_value']) if filter_strategy['max_value'] else float(sys.maxsize)
                    filter_strategies.append(
                        AmountFilterStrategy(min_value, max_value)
                    )
            filters[key] = filter_strategies

        view_config.append({
            'name': name,
            'filters': filters
        })
    logging.info(view_config)
    return view_config
