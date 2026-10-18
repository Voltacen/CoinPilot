"""
Connector stubs for Coinbase sandbox.
This module provides the structure for implementing Coinbase sandbox OAuth and API calls.
Store credentials encrypted in the Integration model and provide helper methods.
"""
import os
import requests

class CoinbaseConnector:
    def __init__(self, credentials=None):
        self.credentials = credentials
        self.base = os.getenv('COINBASE_API_BASE', 'https://api.sandbox.coinbase.com')

    def get_accounts(self):
        # placeholder: return simulated accounts
        return [{'id':'acct_demo','balance':'1000.00','currency':'USD'}]

    def simulate_deposit(self, account_id, amount, memo=None):
        # This does NOT create a real deposit — it simulates and returns a fake result
        return {'status':'simulated', 'account_id':account_id, 'amount':str(amount), 'memo':memo}
