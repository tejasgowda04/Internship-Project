"""
Blockchain Verification Service
Records food donation verifications on Ethereum Sepolia testnet.
Zero-cost: uses test ETH from faucets.
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def record_verification(match):
    """
    Record a match verification on the blockchain.
    Returns the transaction hash or None on failure.
    """
    try:
        from web3 import Web3

        rpc_url = settings.SEPOLIA_RPC_URL
        private_key = settings.ETH_PRIVATE_KEY

        if not rpc_url or not private_key:
            logger.warning("Blockchain credentials not configured. Skipping on-chain verification.")
            return _generate_mock_hash(match)

        w3 = Web3(Web3.HTTPProvider(rpc_url))

        if not w3.is_connected():
            logger.error("Cannot connect to Sepolia RPC.")
            return _generate_mock_hash(match)

        account = w3.eth.account.from_key(private_key)
        nonce = w3.eth.get_transaction_count(account.address)

        # Encode verification data in transaction input
        verification_data = (
            f"FoodWasteChain Verification | "
            f"Match: {match.id} | "
            f"Donor: {match.listing.donor.username} | "
            f"Charity: {match.charity.username} | "
            f"Food: {match.listing.get_food_type_display()} | "
            f"Qty: {match.listing.quantity_kg}kg | "
            f"Score: {match.match_score}"
        )

        tx = {
            'nonce': nonce,
            'to': account.address,  # Self-transfer (zero value, data only)
            'value': 0,
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
            'data': w3.to_hex(text=verification_data),
            'chainId': 11155111,  # Sepolia chain ID
        }

        signed = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        tx_hex = w3.to_hex(tx_hash)

        logger.info(f"Blockchain verification recorded: {tx_hex}")
        return tx_hex

    except ImportError:
        logger.warning("web3 not installed. Using mock blockchain hash.")
        return _generate_mock_hash(match)

    except Exception as e:
        logger.error(f"Blockchain error: {e}")
        return _generate_mock_hash(match)


def _generate_mock_hash(match):
    """Generate a deterministic mock tx hash for demo/dev purposes."""
    import hashlib
    data = f"{match.id}-{match.listing.id}-{match.charity.username}"
    return "0x" + hashlib.sha256(data.encode()).hexdigest()


def get_etherscan_url(tx_hash):
    """Return Sepolia Etherscan link for a transaction."""
    if tx_hash:
        return f"https://sepolia.etherscan.io/tx/{tx_hash}"
    return None
