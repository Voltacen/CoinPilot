import os
from decimal import Decimal

from eth_account import Account
from web3 import Web3

from Config import Config
from app.extensions import db
from app.models.audit import Notification
from app.models.blockchain import BlockchainTransaction


class BlockchainService:
    @staticmethod
    def get_web3_instance(chain_id: int) -> Web3:
        net_cfg = Config.SUPPORTED_NETWORKS.get(chain_id)
        if not net_cfg:
            raise ValueError(f"Chain ID {chain_id} is not supported.")
        w3 = Web3(Web3.HTTPProvider(net_cfg["rpc_url"], request_kwargs={"timeout": 15}))
        if not w3.is_connected():
            raise ConnectionError(f"Unable to connect to RPC node for chain {chain_id}.")
        return w3

    @staticmethod
    def get_platform_native_balance(chain_id: int) -> Decimal:
        w3 = BlockchainService.get_web3_instance(chain_id)
        signer_key = os.getenv("PLATFORM_TESTNET_SIGNER_KEY")
        if not signer_key:
            return Decimal("0.0")
        acct = Account.from_key(signer_key)
        balance_wei = w3.eth.get_balance(acct.address)
        return Decimal(str(w3.from_wei(balance_wei, "ether")))

    @staticmethod
    def dispatch_testnet_transfer(user_id: str, chain_id: int, recipient_address: str, amount_ether: Decimal, idempotency_key: str):
        if amount_ether <= Decimal("0"):
            raise ValueError("Transfer amount must be greater than zero.")

        w3 = BlockchainService.get_web3_instance(chain_id)
        if not w3.is_address(recipient_address):
            raise ValueError("Invalid destination EVM address.")

        recipient_checksum = w3.to_checksum_address(recipient_address)
        signer_key = os.getenv("PLATFORM_TESTNET_SIGNER_KEY")
        if not signer_key:
            raise ValueError("Platform testnet signer key not configured in environment.")

        platform_account = Account.from_key(signer_key)

        existing_tx = BlockchainTransaction.query.filter_by(idempotency_key=idempotency_key).first()
        if existing_tx:
            return existing_tx

        tx_record = BlockchainTransaction(
            user_id=user_id,
            chain_id=chain_id,
            token_symbol="ETH",
            sender_address=platform_account.address,
            recipient_address=recipient_checksum,
            amount_in_units=amount_ether,
            status="Created",
            idempotency_key=idempotency_key,
        )
        db.session.add(tx_record)
        db.session.commit()

        try:
            value_wei = w3.to_wei(amount_ether, "ether")
            nonce = w3.eth.get_transaction_count(platform_account.address, "pending")
            gas_price = w3.eth.gas_price

            tx_dict = {
                "nonce": nonce,
                "to": recipient_checksum,
                "value": value_wei,
                "gas": 21000,
                "gasPrice": gas_price,
                "chainId": chain_id,
            }

            signed_tx = w3.eth.account.sign_transaction(tx_dict, private_key=signer_key)
            tx_hash_bytes = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash_hex = w3.to_hex(tx_hash_bytes)

            tx_record.tx_hash = tx_hash_hex
            tx_record.nonce = nonce
            tx_record.status = "Submitted"
            db.session.commit()

            receipt = w3.eth.wait_for_transaction_receipt(tx_hash_bytes, timeout=120)
            if receipt.get("status") == 1:
                tx_record.status = "Successful"
                tx_record.block_number = receipt.get("blockNumber")
                tx_record.gas_used = receipt.get("gasUsed")
                db.session.add(Notification(
                    user_id=user_id,
                    title="Blockchain Transaction Confirmed",
                    message=f"Sent {amount_ether} SepoliaETH to {recipient_checksum[:10]}... Tx: {tx_hash_hex[:12]}...",
                    category="SUCCESS",
                ))
            else:
                tx_record.status = "Failed"
                tx_record.error_message = "EVM reverted transaction on-chain."

            db.session.commit()
            return tx_record

        except Exception as exc:
            tx_record.status = "Failed"
            tx_record.error_message = str(exc)
            db.session.commit()
            raise exc
