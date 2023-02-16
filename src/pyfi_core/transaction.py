from datetime import datetime
import logging


class Transaction:
    def __init__(self):
        self.valid = True
        self.source_account = ""
        self.transaction_date = datetime.min
        self.posting_date = datetime.min
        self.counterparty_data = ""
        self.title = ""
        self.target_account = ""
        self.bank_name = ""
        self.details = ""
        self.transaction_number = ""
        self.amount = float(0)
        self.currency = ""
        self.lock_amount = ""
        self.lock_currency = ""
        self.payment_amount = ""
        self.payment_currency = ""
