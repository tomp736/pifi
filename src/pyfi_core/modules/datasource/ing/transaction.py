from datetime import datetime
import logging


class Transaction:
    def __init__(self, data, account_number):
        self.valid = True
        try:
            self.account_number = account_number.strip("'").strip().replace(" ","")

            try:
                self.transaction_date = datetime.strptime(
                    data['Data transakcji'], '%Y-%m-%d')
            except ValueError:
                self.transaction_date = None
                self.valid = False

            try:
                self.posting_date = datetime.strptime(
                    data['Data księgowania'], '%Y-%m-%d')
            except ValueError:
                self.posting_date = None
                self.valid = False

            self.counterparty_data = data['Dane kontrahenta'].strip("'").strip()
            self.title = data['Tytuł'].strip("'").strip()
            self.account = data['Nr rachunku'].strip("'").strip()
            self.bank_name = data['Nazwa banku'].strip("'").strip()
            self.details = data['Szczegóły'].strip("'").strip()
            self.transaction_number = data['Nr transakcji'].strip("'").strip()
            

            try:
                self.amount = float(
                data['Kwota transakcji (waluta rachunku)'].replace(',', '.'))
            except ValueError:
                self.amount = 0
                
            
            self.currency = data['Waluta'].strip("'").strip()
            self.lock_amount = data['Kwota blokady/zwolnienie blokady'].strip("'").strip()
            self.lock_currency = data['Waluta'].strip("'").strip()
            self.payment_amount = data['Kwota płatności w walucie'].strip("'").strip()
            self.payment_currency = data['Waluta'].strip("'").strip()
        except Exception as ex:
            logging.error(f"Error parsing data: {data}: {ex}")
            self.valid = False
