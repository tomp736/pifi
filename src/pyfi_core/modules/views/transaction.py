from datetime import timedelta, date, datetime
import logging
import re
import threading

# todo - extract and implement with external datasource


class ExchangeRateProvider:
    def convert_currency(self, amount, from_currency, to_currency):
        if from_currency == "":
            from_currency = "PLN"

        if from_currency == "PLN" and to_currency == "EUR":
            return True, amount / 5
        if from_currency == "PLN" and to_currency == "USD":
            return True, amount / 4
        if from_currency == "EUR" and to_currency == "PLN":
            return True, amount * 5
        if from_currency == "USD" and to_currency == "PLN":
            return True, amount * 4
        return False, amount


class TransactionTransformStrategy:
    def transform_transactions(self, transactions):
        pass


class CurrencyTranformStrategy(TransactionTransformStrategy):
    def __init__(self, target_currency, exchange_rate_provider: ExchangeRateProvider):
        self.exchange_rate_provider = exchange_rate_provider
        self.target_currency = target_currency

    def transform_transactions(self, transactions):
        for transaction in transactions:
            if transaction.currency != self.target_currency:
                success, amount = self.exchange_rate_provider.convert_currency(
                    transaction.amount, transaction.currency, self.target_currency)
                if success:
                    logging.info(
                        f"Transform: {transaction.currency} to {self.target_currency} {transaction.amount} -> {amount}")
                    transaction.transform_currency = transaction.currency
                    transaction.transform_amount = transaction.amount
                    transaction.currency = self.target_currency
                    transaction.amount = amount


class TransactionFilterStrategy:
    def filter_transactions(self, transactions):
        pass


class RegexFieldFilterStrategy(TransactionFilterStrategy):
    def __init__(self, field_name, regex, flags=re.IGNORECASE):
        self.field_name = field_name
        self.regex = regex
        self.flags = flags

    def filter_transactions(self, transactions):
        filtered_transactions = []
        for transaction in transactions:
            field_value = getattr(transaction, self.field_name)
            if re.search(self.regex, field_value, self.flags):
                filtered_transactions.append(transaction)
        return filtered_transactions


class DateFilterStrategy(TransactionFilterStrategy):
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date

    def filter_transactions(self, transactions):
        filtered_transactions = []
        for transaction in transactions:
            if self.start_date <= transaction.transaction_date <= self.end_date:
                filtered_transactions.append(transaction)
        return filtered_transactions


class AccountFilterStrategy(TransactionFilterStrategy):
    def __init__(self, account_number):
        self.account_number = account_number

    def filter_transactions(self, transactions):
        filtered_transactions = []
        for transaction in transactions:
            if transaction.account_number == self.account_number:
                filtered_transactions.append(transaction)
        return filtered_transactions

class TransactionViewBuilder:
    def __init__(self, transactions):
        self.transactions = transactions
        self.transaction_filters = []
        self.transaction_transforms = []
        self.start_date = date.min
        self.end_date = date.max
        self.time_delta = timedelta(days=1)

    def set_duration(self, start_date: date, end_date: date, time_delta: timedelta):
        self.start_date = start_date
        self.end_date = end_date
        self.time_delta = time_delta

    def add_filter(self, transaction_filter: TransactionFilterStrategy):
        self.transaction_filters.append(transaction_filter)

    def add_transform(self, transaction_transform: TransactionTransformStrategy):
        self.transaction_transforms.append(transaction_transform)

    def add_transforms(self, transaction_transforms):
        self.transaction_transforms += transaction_transforms

    def add_filters(self, transaction_filters):
        self.transaction_filters += transaction_filters

    def clear_filters(self):
        self.transaction_filters = []

    def get_views(self):
        views = []
        # get outer view transactions
        outer_view = TransactionView(self.transactions, self.start_date, self.end_date, [
                                     DateFilterStrategy(self.start_date, self.end_date)])
        current_date = self.start_date
        while current_date <= self.end_date:
            next_date = current_date + self.time_delta
            t = threading.Thread(target=process_view, args=(
                current_date, next_date, outer_view.transactions, self.transaction_filters, self.transaction_transforms, views))
            t.start()
            current_date = next_date
        t.join()
        return views

    def get_config_views(self, view_config):
        transaction_views = []
        threads = []
        for category in view_config:
            category_name = category['name']
            category_filters = category['filters']
            t = threading.Thread(target=process_category, args=(
                category_name, category_filters, transaction_views, self))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        return transaction_views    

def process_category(category_name, category_filters, transaction_views, parent_tvb):
    logging.info(f"processing {category_name}")
    for sub_category_name, category_filters in category_filters.items():
        category_tvb = TransactionViewBuilder(parent_tvb.transactions)
        category_tvb.set_duration(parent_tvb.start_date, parent_tvb.end_date, parent_tvb.time_delta)
        category_tvb.add_filters(parent_tvb.transaction_filters + category_filters)
        category_tvb.add_transforms(parent_tvb.transaction_transforms)
        category_tvb_views = category_tvb.get_views()
        for view in category_tvb_views:
            view.category = category_name
            view.subcategory = sub_category_name
            view.filter_name = category_name
        transaction_views += category_tvb_views
    logging.info(f"processing {category_name}: end")


def process_view(current_date, next_date, transactions, transaction_filters, transaction_transforms, views):
    date_filter = DateFilterStrategy(start_date=current_date, end_date=next_date)
    transaction_view = TransactionView(transactions, current_date, next_date, transaction_filters + [date_filter], transaction_transforms)
    if transaction_view.has_data:
        views.append(transaction_view)


class TransactionViewCollection:
    def __init__(self, transaction_views, start_date, end_date):
        self.transaction_views = transaction_views
        self.start_date = start_date
        self.end_date = end_date


class TransactionView:
    def __init__(self, transactions, start_date, end_date, filter_strategies=[], transaction_transforms=[]):
        self.has_data = False
        self.income = 0
        self.expense = 0
        self.start_date = start_date
        self.end_date = end_date
        self.transactions = transactions
        self.filter_strategies = filter_strategies
        self.transaction_transforms = transaction_transforms
        self.filter(self.filter_strategies)
        self.transform(self.transaction_transforms)
        self.calculate()

    def transform(self, transaction_transforms):
        if transaction_transforms is not None:
            for transaction_transform in transaction_transforms:
                transaction_transform.transform_transactions(self.transactions)

    def filter(self, filter_strategies):
        if filter_strategies is not None:
            for filter_strategy in filter_strategies:
                self.transactions = filter_strategy.filter_transactions(
                    self.transactions)
        return self

    def calculate(self):
        for transaction in self.transactions:
            self.has_data = True

            if transaction.amount > 0:
                self.income += transaction.amount
            else:
                self.expense += transaction.amount
