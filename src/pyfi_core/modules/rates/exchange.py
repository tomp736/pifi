

from abc import abstractmethod
from bisect import bisect_left
from datetime import date, timedelta
import datetime
import logging
import os

import requests


class ExchangeRateProvider:

    def __init__(self) -> None:
        self.currency_base = 'USD'

    @abstractmethod
    def get_exchange_rates(self, currency_date: date) -> dict:
        pass

    def convert_currency(self, exchange_rates, base_currency, amount, from_currency, to_currency):
        # If the currencies are the same, return the original amount
        if from_currency == to_currency:
            logging.info("Coverting0")
            return amount

        # If the target currency is the base currency, return the amount times the exchange rate for the source currency
        if to_currency == base_currency:
            logging.info("Coverting1")
            return amount / exchange_rates[from_currency]

        # If the source currency is the base currency, return the amount times the exchange rate for the target currency
        if from_currency == base_currency:
            logging.info("Coverting2")
            return amount * exchange_rates[to_currency]

        # If neither the source nor target currency is the base currency, convert to USD first
        amount_usd = amount / exchange_rates[from_currency]
        logging.info("Coverting3")
        return amount_usd * exchange_rates[to_currency]


class MockExchangeRateProvider(ExchangeRateProvider):

    def get_exchange_rates(self, currency_date: date) -> dict:
        return {
            "EUR": 0.967972,
            "PLN": 4.553055,
        }


class OpenExchangeRateProvider(ExchangeRateProvider):

    def __init__(self) -> None:
        super().__init__()
        self.app_id = os.environ.get("OPENEXCHANGERATES_APP_ID")

    def get_exchange_rates(self, currency_date: date) -> dict:
        currency_date_str = currency_date.strftime('%Y-%m-%d')
        request_url = f'https://openexchangerates.org/api/historical/{currency_date_str}.json?app_id={self.app_id}'
        response = requests.get(request_url)
        return response.json()['rates']


class CachedOpenExchangeRatesProvider(OpenExchangeRateProvider):

    def __init__(self):
        super().__init__()
        self.cache = {}

    def get_exchange_rates(self, currency_date: date) -> dict:
        # Check if the exchange rates for the specified date and base currency are already cached
        cache_key = f'{currency_date:%Y-%m-%d}'
        if cache_key in self.cache:
            return self.cache[cache_key]

        # If the exchange rates are not cached, get them from the parent class
        rates = super().get_exchange_rates(currency_date)

        # Cache the exchange rates for future use
        self.cache[cache_key] = rates

        return rates

# linear fit provider - reduces resultion to give rates without exceeding api limits


class LinearFitOpenExchangeRatesProvider(OpenExchangeRateProvider):

    def __init__(self, start_date: date, end_date: date, time_delta: timedelta):
        super().__init__()
        self.cache = []
        self.start_date = start_date
        self.end_date = end_date
        self.time_delta = time_delta
        self.build_cache()

    def build_cache(self):
        current_date = self.start_date
        while current_date <= self.end_date:
            next_date = current_date + self.time_delta

            try:
                exchange_rates = super().get_exchange_rates(current_date)
                timestamp = int(datetime.datetime(
                    current_date.year, current_date.month, current_date.day).timestamp())
                self.cache.append({
                    'timestamp': timestamp,
                    'source': 'openexchangerates',
                    'rates': exchange_rates
                })
            except Exception as ex:
                logging.info(ex)

            current_date = next_date

    def get_exchange_rates(self, currency_date: date) -> dict:
        currency = self.currency_base
        timestamp = int(datetime.datetime(currency_date.year,
                        currency_date.month, currency_date.day).timestamp())
        timestamps = [item['timestamp'] for item in self.cache]
        index = bisect_left(timestamps, timestamp)

        # If the date is before the first known date, use the first known exchange rate
        if index == 0:
            rates = self.cache[index]['rates']
        # If the date is after the last known date, use the last known exchange rate
        elif index == len(self.cache):
            rates = self.cache[-1]['rates']
        # If the date is within the bounds, use the corresponding exchange rate
        else:
            # Get the exchange rates for the closest known dates
            prev_rates = self.cache[index - 1]['rates']
            next_rates = self.cache[index]['rates']

            # Calculate the weights for the linear fit
            prev_weight = (timestamps[index] - timestamp) / \
                (timestamps[index] - timestamps[index - 1])
            next_weight = 1 - prev_weight

            # Approximate the exchange rate using a linear fit
            rates = {currency: prev_weight * prev_rates[currency] + next_weight * next_rates[currency]
                     for currency in prev_rates}

        return rates
