import csv

from pyfi_core.modules.datasource.ing.transaction import Transaction

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
                    transaction = Transaction(row_dict, self.account_number)
                    if transaction.valid:
                        transactions.append(transaction)
        return transactions
