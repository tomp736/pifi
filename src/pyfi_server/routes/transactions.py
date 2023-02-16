from datetime import date, timedelta
import datetime
import json
import logging
import os
from venv import logger

from flask import Blueprint, render_template, request
from flask import Response
from pyfi_core.modules.datasource.ing.transaction_reader import TransactionReader
from pyfi_core.modules.views.config import read_view_config
from pyfi_core.modules.datasource.config import read_datasource_config

from pyfi_core.modules.views.transaction import CurrencyTranformStrategy, DateFilterStrategy, ExchangeRateProvider, RegexFieldFilterStrategy, TransactionView, TransactionViewCollection, TransactionViewBuilder
from pyfi_server.constants import VIEWS_PATH
from pyfi_server.constants import DATASOURCE_PATH

app_frontend_transaction = Blueprint('app_frontend_transaction', __name__)

@app_frontend_transaction.route('/')
def get_index():
    return render_template('index.html')


@app_frontend_transaction.route('/api/transaction/view')
def get_transaction_view():
    transactions = []
    datasource_config = read_datasource_config(DATASOURCE_PATH)
    for datasource in datasource_config:
        path = datasource['path']
        for filename in os.listdir(path):
            if os.path.isfile(os.path.join(path, filename)):
                csv_reader = TransactionReader(os.path.join(path, filename))
                transactions += csv_reader.read_transactions()

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
    view_config = read_view_config(VIEWS_PATH)

    exchange_rate_provider = ExchangeRateProvider()
    transaction_transform_currency = CurrencyTranformStrategy(
        "PLN", exchange_rate_provider)

    transaction_views = []

    for category in view_config:
        category_name = category['name']
        category_filters = category['filters']
        logging.info(category_name)
        for filter_name, transaction_view_filters in category_filters.items():
            transaction_view_builder = TransactionViewBuilder(transactions)
            transaction_view_builder.set_duration(
                start_date, end_date, timedelta(days=time_delta_d))
            transaction_view_builder.add_transform(
                transaction_transform_currency)
            transaction_view_builder.add_filters(transaction_view_filters)
            transaction_view_builder_views = transaction_view_builder.get_views()
            for view in transaction_view_builder_views:
                view.category = category_name
                view.filter_name = filter_name
            transaction_views += transaction_view_builder_views

    # for category, transaction_view_filters in food_category_filters.items():
    #     transaction_view_builder.add_filters(transaction_view_filters)
    #     transaction_views += transaction_view_builder.get_views()
    #     transaction_view_builder.clear_filters()

    return_tvc = TransactionViewCollection(
        transaction_views, start_date, end_date)

    json_response = json.dumps(
        return_tvc, cls=TransactionViewCollectionEncoder, sort_keys=True, indent=4)
    return Response(json_response, status=200, content_type="application/json")


class TransactionViewEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, list):
            return [TransactionViewEncoder().default(item) for item in obj]
        if isinstance(obj, DateFilterStrategy):
            return DateFilterStrategyEncoder().default(obj)
        if isinstance(obj, TransactionView):
            return {'category': obj.category, 'income': obj.income, 'expense': obj.expense, 'start_date': obj.start_date.isoformat(), 'end_date': obj.end_date.isoformat()}
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
