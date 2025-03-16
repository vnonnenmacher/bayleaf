from web3 import Web3
from django.conf import settings

# Connect to Private Ethereum Node
w3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER))

# Contract ABI and Address (Replace with actual contract ABI and address)
CONTRACT_ABI = settings.BLOCKCHAIN_CONTRACT_ABI
CONTRACT_ADDRESS = settings.BLOCKCHAIN_CONTRACT_ADDRESS

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)


class SampleBlockchain:
    """
    Interface for interacting with the blockchain to store and retrieve sample state transitions.
    """

    @staticmethod
    def record_transition(sample_id, previous_state, new_state, sender):
        """Records a sample state transition on the blockchain."""
        tx_hash = contract.functions.addTransition(
            str(sample_id),
            previous_state if previous_state else "None",
            new_state
        ).transact({'from': sender})

        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        return {
            "transaction_hash": tx_receipt.transactionHash.hex(),
            "blockchain_timestamp": tx_receipt.blockNumber,
            "is_verified": True
        }

    @staticmethod
    def get_transition_count():
        """Returns the total number of recorded sample transitions."""
        return contract.functions.getTransitionCount().call()
