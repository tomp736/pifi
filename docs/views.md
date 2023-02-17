``` json
[
    {
      "name": "bills",
      "filters": {
        "RENT": [
          {
            "type": "RegexFieldFilterStrategy",
            "field_name": "title",
            "regex": ".*Inflancka.*"
          }
        ],
        "INTERNET": [
          {
            "type": "RegexFieldFilterStrategy",
            "field_name": "counterparty_data",
            "regex": ".*BLUEMEDIA*"
          },
          {
            "type": "RegexFieldFilterStrategy",
            "field_name": "title",
            "regex": ".*orange*"
          }
        ]
      }
    }
]
```