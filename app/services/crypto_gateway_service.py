import os
from decimal import Decimal

from eth_account import Account
from web3 import Web3

from Config import Config


class CryptoGatewayService:
    @staticmethod
    def get_rpc_url(chain_id: int) -> str:
        net = Config.SUPPORTED_NETWORKS.get(chain_id)
        if not net:
            raise ValueError(f"Unsupported chain ID: {chain_id}")
        return net["rpc_url"]

    @staticmethod
    def validate_address(chain_id: int, address: str) -> bool:
        rpc_url = CryptoGatewayService.get_rpc_url(chain_id)
        w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 20}))
        return bool(w3.is_address(address))

    @staticmethod
    def get_native_balance(chain_id: int, address: str) -> Decimal:
        rpc_url = CryptoGatewayService.get_rpc_url(chain_id)
        w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 20}))
        balance_wei = w3.eth.get_balance(address)
        return Decimal(str(w3.from_wei(balance_wei, "ether")))

    @staticmethod
    def send_testnet_transfer(chain_id: int, recipient_address: str, amount_eth: Decimal):
        private_key = os.getenv("PLATFORM_TESTNET_SIGNER_KEY")
        if not private_key:
            raise ValueError("Platform hot wallet is not configured.")

        rpc_url = CryptoGatewayService.get_rpc_url(chain_id)
        w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 20}))

        if not w3.is_address(recipient_address):
            raise ValueError("Recipient address is not valid for the selected chain.")

        account = Account.from_key(private_key)
        tx = {
            "to": recipient_address,
            "value": w3.to_wei(amount_eth, "ether"),
            "gas": 21000,
            "gasPrice": w3.eth.gas_price,
            "nonce": w3.eth.get_transaction_count(account.address),
            "chainId": chain_id,
        }
        signed = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        return w3.to_hex(tx_hash)
