from datetime import date, timedelta
import datetime
import json
import logging
import os
from pyfi_core.modules.datasource.config import read_file as read_datasource_config_file
from pyfi_core.modules.views.config import read_file as read_dataviews_config_file
from pyfi_core.modules.views.config import read_json as read_dataviews_json
from venv import logger

from flask import Blueprint, render_template, request
from flask import Response

from pyfi_core.modules.views.transaction import CurrencyTranformStrategy, DateFilterStrategy, ExchangeRateProvider, RegexFieldFilterStrategy, TransactionView, TransactionViewCollection, TransactionViewBuilder
from pyfi_server.constants import VIEWS_PATH
from pyfi_server.constants import DATASOURCE_PATH

app_frontend_transaction = Blueprint('app_frontend_transaction', __name__)

# Global variable to store the JSON data
CONFIG_DATAVIEWS = []


@app_frontend_transaction.route('/')
def get_index():
    return render_template('index.html')


@app_frontend_transaction.route('/api/config/views', methods=['POST'])
def update_config_dataviews():
    global CONFIG_DATAVIEWS
    CONFIG_DATAVIEWS = request.get_json()
    return Response(status=200)


@app_frontend_transaction.route('/api/transaction/view')
def get_transaction_view():
    start_date = date.min
    try:
        if 'start_date' in request.args.keys():
            s_start_date = request.args.get('start_date')
            start_date = datetime.datetime.strptime(s_start_date, '%Y-%m-%d')
    except:
        logger.info("Error parsing")

    end_date = date.today()
    try:
        if 'end_date' in request.args.keys():
            s_end_date = request.args.get('end_date')
            end_date = datetime.datetime.strptime(s_end_date, '%Y-%m-%d')
    except:
        logger.info("Error parsing")

    time_delta_d = 30
    try:
        if 'time_delta_d' in request.args.keys():
            s_time_delta_d = request.args.get('time_delta_d')
            time_delta_d = int(s_time_delta_d)
    except:
        logger.info("Error parsing")

    # categories - built on filters

    return_tvc = process_request(start_date, end_date, time_delta_d)

    json_response = json.dumps(
        return_tvc, cls=TransactionViewCollectionEncoder, sort_keys=True, indent=4)
    return Response(json_response, status=200, content_type="application/json")

def process_request(start_date, end_date, time_delta_d):
    transactions = []
    datasource_configs = read_datasource_config_file(DATASOURCE_PATH)
    view_config = read_dataviews_json(CONFIG_DATAVIEWS)
    for datasource_config in datasource_configs:
        transactions += datasource_config['datasource'].read_data()
        
    exchange_rate_provider = ExchangeRateProvider()
    transaction_transform_currency = CurrencyTranformStrategy(
        "PLN", exchange_rate_provider)

    transaction_views = []
    transaction_view_builder = TransactionViewBuilder(transactions)
    transaction_view_builder.set_duration(
        start_date, end_date, timedelta(days=time_delta_d))
    transaction_view_builder.add_transform(transaction_transform_currency)
    transaction_views = transaction_view_builder.get_config_dataviews(view_config)

    return_tvc = TransactionViewCollection(
        transaction_views, start_date, end_date)
        
    return return_tvc


class TransactionViewEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, list):
            return [TransactionViewEncoder().default(item) for item in obj]
        if isinstance(obj, DateFilterStrategy):
            return DateFilterStrategyEncoder().default(obj)
        if isinstance(obj, TransactionView):
            return {'metadata': obj.metadata, 'income': obj.income, 'expense': obj.expense, 'start_date': obj.start_date.isoformat(), 'end_date': obj.end_date.isoformat()}
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


class TransactionViewCollectionEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, TransactionViewCollection):
            return [TransactionViewEncoder().default(view) for view in obj.transaction_views]
        return json.JSONEncoder.default(self, obj)


class DateFilterStrategyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, DateFilterStrategy):
            return {'start_date': obj.start_date.isoformat(), 'end_date': obj.end_date.isoformat()}
        return json.JSONEncoder.default(self, obj)


@app_frontend_transaction.after_request
def after_request(response):
    response.headers.set('Accept-Ranges', 'bytes')
    response.headers.set('Access-Control-Allow-Origin', "*")
    return response
