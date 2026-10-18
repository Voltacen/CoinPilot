"""
Connector stubs for Binance testnet.
"""
import os

class BinanceConnector:
    def __init__(self, credentials=None):
        self.credentials = credentials
        self.base = os.getenv('BINANCE_API_BASE', 'https://testnet.binance.vision')

    def get_account(self):
        return {'accountId':'demo', 'balances':[{'asset':'BTC','free':'0.000','locked':'0.000'}]}

    def simulate_deposit(self, account_id, asset, amount):
        return {'status':'simulated', 'account_id':account_id, 'asset':asset, 'amount':str(amount)}
