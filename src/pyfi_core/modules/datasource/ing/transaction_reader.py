import csv
import datetime
import logging

from pyfi_core.transaction import Transaction

class TransactionReader:
    def __init__(self, file_path, encoding = 'windows-1250'):
        self.file_path = file_path
        self.account_number = None
        self.encoding = encoding

    def read_transactions(self):
        transactions = []
        with open(self.file_path, 'r', encoding=self.encoding) as csv_file:
            headers = []
            csv_reader = csv.reader(csv_file, delimiter=';')
            row_number = 0
            for row in csv_reader:
                if row_number == 8:
                    self.account_number = row[2]
                elif row_number == 18:
                    headers = [header.strip() for header in row]
                    break
                row_number += 1

            transactions = []
            for row in csv_reader:
                if len(row) == len(headers):
                    row_dict = {headers[i]: row[i].strip() for i in range(len(headers))}
                    transaction = self.read_transaction_data(row_dict, self.account_number)
                    if transaction.valid:
                        transactions.append(transaction)
        return transactions
    
    def read_transaction_data(self, data, source_account):
        transaction = Transaction()
        
        transaction.valid = True
        try:
            transaction.source_account = source_account.strip("'").strip().replace(" ","")

            try:
                transaction.transaction_date = datetime.datetime.strptime(
                    data['Data transakcji'], '%Y-%m-%d')
            except ValueError:
                transaction.valid = False

            try:
                transaction.posting_date = datetime.datetime.strptime(
                    data['Data księgowania'], '%Y-%m-%d')
            except ValueError:
                transaction.valid = False

            transaction.counterparty_data = data['Dane kontrahenta'].strip("'").strip()
            transaction.title = data['Tytuł'].strip("'").strip()
            transaction.account = data['Nr rachunku'].strip("'").strip()
            transaction.bank_name = data['Nazwa banku'].strip("'").strip()
            transaction.details = data['Szczegóły'].strip("'").strip()
            transaction.transaction_number = data['Nr transakcji'].strip("'").strip()
            

            try:
                transaction.amount = float(
                data['Kwota transakcji (waluta rachunku)'].replace(',', '.'))
            except ValueError:
                transaction.amount = 0
                
            
            transaction.currency = data['Waluta'].strip("'").strip()
            transaction.lock_amount = data['Kwota blokady/zwolnienie blokady'].strip("'").strip()
            transaction.lock_currency = data['Waluta'].strip("'").strip()
            transaction.payment_amount = data['Kwota płatności w walucie'].strip("'").strip()
            transaction.payment_currency = data['Waluta'].strip("'").strip()
        except Exception as ex:
            logging.error(f"Error parsing data: {data}: {ex}")
            transaction.valid = False
            
        return transaction
