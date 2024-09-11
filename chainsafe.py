import requests
import json
import time
import logging
import zksync
from zksync import (
    Wallet,
    ZkSyncProvider,
    ZkSyncTransaction,
    ZkSyncTxReceipt,
)
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Setup logging for error tracking and info
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ChainSafe API endpoints
data_upload_endpoint = "https://your-chainsafe-api.com/upload"
data_query_endpoint = "https://your-chainsafe-api.com/query"

# ZkSync configuration
zk_sync_provider = ZkSyncProvider("https://zksync2-testnet.zksync.io")
private_key = "your_private_key"
wallet = Wallet(private_key, zk_sync_provider)

# SQLAlchemy setup
engine = create_engine('your_database_connection_string')
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

# Define SQLAlchemy model classes
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    total_amount = Column(Integer)
    created_at = Column(DateTime)

# Create the database schema if it doesn't exist
Base.metadata.create_all(engine)

# Function to upload patient data to ChainSafe
def upload_patient_data(patient_data):
    try:
        response = requests.post(data_upload_endpoint, json=patient_data)
        if response.status_code == 200:
            logging.info(f"Data uploaded successfully: {response.json()['data_id']}")
            return response.json()["data_id"]
        else:
            logging.error(f"Data upload failed with status code: {response.status_code}")
            raise Exception("Data upload failed")
    except Exception as e:
        logging.exception("Error during data upload")
        raise e

# Function to query patient data from ChainSafe
def query_patient_data(data_id):
    try:
        response = requests.get(data_query_endpoint, params={"data_id": data_id})
        if response.status_code == 200:
            logging.info(f"Data retrieved successfully for ID: {data_id}")
            return response.json()["data"]
        else:
            logging.error(f"Data query failed with status code: {response.status_code}")
            raise Exception("Data query failed")
    except Exception as e:
        logging.exception("Error during data query")
        raise e

# Function to mint a token representing patient data on ZkSync
def mint_token(data_id):
    try:
        transaction = ZkSyncTransaction(
            to="your_token_contract_address",
            value=0,
            data=b"0x0000000000000000000000000000000000000000000000000000000000000001",
            nonce=wallet.get_nonce(),
            max_fee=1000000,  # Adjust max fee as needed
        )
        signed_transaction = wallet.sign_transaction(transaction)
        receipt = zk_sync_provider.send_transaction(signed_transaction)
        logging.info(f"Token minted successfully: {receipt.tx_hash}")
        return receipt
    except Exception as e:
        logging.exception("Error during token minting")
        raise e

# Function to transfer a token on ZkSync
def transfer_token(token_id, recipient_address):
    try:
        transaction = ZkSyncTransaction(
            to="your_token_contract_address",
            value=0,
            data=b"0xa9059cbb" + recipient_address.encode().hex() + token_id.encode().hex(),
            nonce=wallet.get_nonce(),
            max_fee=1000000,  # Adjust max fee as needed
        )
        signed_transaction = wallet.sign_transaction(transaction)
        receipt = zk_sync_provider.send_transaction(signed_transaction)
        logging.info(f"Token transferred successfully: {receipt.tx_hash}")
        return receipt
    except Exception as e:
        logging.exception("Error during token transfer")
        raise e

# Function to store and retrieve user and order information
def add_user_and_order(name, email, total_amount):
    try:
        # Add new user
        new_user = User(name=name, email=email)
        session.add(new_user)
        session.commit()

        # Add a new order for the user
        new_order = Order(user_id=new_user.id, total_amount=total_amount, created_at=func.now())
        session.add(new_order)
        session.commit()

        logging.info(f"User {name} and their order added successfully.")
    except Exception as e:
        logging.exception("Error adding user and order to the database")
        session.rollback()
        raise e

# Main function to demonstrate the workflow
def main():
    try:
        # Patient data (replace with actual data)
        patient_data = {
            "name": "John Doe",
            "age": 30,
            "medical_history": "...",
        }

        # Upload data to ChainSafe
        data_id = upload_patient_data(patient_data)

        # Mint a token on ZkSync
        receipt = mint_token(data_id)
        print("Token minted successfully: ", receipt.tx_hash)

        # Transfer the token to a recipient
        recipient_address = "0x0000000000000000000000000000000000000000"  # Replace with actual recipient address
        receipt = transfer_token(data_id, recipient_address)
        print("Token transferred successfully: ", receipt.tx_hash)

        # Add a user and an order to the database
        add_user_and_order(name="Jane Doe", email="jane@example.com", total_amount=100)

    except Exception as e:
        logging.error("An error occurred during the workflow", exc_info=True)




# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define Safe Chain metadata (e.g., safe chain ID and contract addresses)
SAFE_CHAIN_METADATA = {
    "chain_id": "0x1",  # Example chain ID for Ethereum mainnet
    "trusted_contracts": [
        "0x1234567890abcdef1234567890abcdef12345678",  # Example trusted contract address
        "0xabcdefabcdefabcdefabcdefabcdefabcdefabcdef"
    ],
    "safe_consensus_protocol": "PoS",  # Proof of Stake
}

# API endpoint to get the current chain metadata (adjust with actual API)
CHAIN_METADATA_ENDPOINT = "https://api.blockchain.info/chain/metadata"

# Function to get the current chain metadata
def get_current_chain_metadata():
    try:
        response = requests.get(CHAIN_METADATA_ENDPOINT)
        if response.status_code == 200:
            logging.info("Successfully retrieved chain metadata")
            return response.json()
        else:
            logging.error(f"Failed to retrieve chain metadata, status code: {response.status_code}")
            raise Exception("Error fetching chain metadata")
    except Exception as e:
        logging.exception("Exception occurred while fetching chain metadata")
        raise e

# Function to check if the chain ID matches the safe chain ID
def check_chain_id(current_chain_id):
    if current_chain_id == SAFE_CHAIN_METADATA["chain_id"]:
        logging.info(f"Chain ID matches the safe chain: {current_chain_id}")
        return True
    else:
        logging.warning(f"Chain ID does not match. Expected {SAFE_CHAIN_METADATA['chain_id']}, got {current_chain_id}")
        return False

# Function to check if all trusted contracts are deployed on the current chain
def check_trusted_contracts(current_contracts):
    safe_contracts = SAFE_CHAIN_METADATA["trusted_contracts"]
    matched_contracts = [contract for contract in safe_contracts if contract in current_contracts]

    if len(matched_contracts) == len(safe_contracts):
        logging.info("All trusted contracts are present on the current chain")
        return True
    else:
        missing_contracts = set(safe_contracts) - set(matched_contracts)
        logging.warning(f"Missing trusted contracts: {missing_contracts}")
        return False

# Function to check if the current chain uses the safe consensus protocol
def check_consensus_protocol(current_protocol):
    if current_protocol == SAFE_CHAIN_METADATA["safe_consensus_protocol"]:
        logging.info(f"Consensus protocol matches: {current_protocol}")
        return True
    else:
        logging.warning(f"Consensus protocol mismatch. Expected {SAFE_CHAIN_METADATA['safe_consensus_protocol']}, got {current_protocol}")
        return False

# Main function to check if the current chain is the safe chain
def check_if_safe_chain():
    try:
        # Fetch current chain metadata
        chain_metadata = get_current_chain_metadata()

        # Extract current chain parameters
        current_chain_id = chain_metadata.get("chain_id")
        current_contracts = chain_metadata.get("deployed_contracts", [])
        current_protocol = chain_metadata.get("consensus_protocol")

        # Perform checks against safe chain metadata
        is_chain_id_safe = check_chain_id(current_chain_id)
        are_contracts_safe = check_trusted_contracts(current_contracts)
        is_consensus_safe = check_consensus_protocol(current_protocol)

        # Final determination if the current chain is safe
        if is_chain_id_safe and are_contracts_safe and is_consensus_safe:
            logging.info("The current chain is on the safe chain.")
            return True
        else:
            logging.warning("The current chain is NOT on the safe chain.")
            return False

    except Exception as e:
        logging.error("Error occurred while checking if the chain is safe", exc_info=True)
        return False

# Example usage of the functionality
if __name__ == "__main__":
    is_safe = check_if_safe_chain()
    if is_safe:
        print("The current chain is SAFE.")
    else:
        print("The current chain is NOT safe.")



logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API endpoint to get block information (adjust with actual API)
GENESIS_BLOCK_ENDPOINT = "https://api.blockchain.info/block/genesis"

# Function to fetch genesis block information
def get_genesis_block():
    try:
        response = requests.get(GENESIS_BLOCK_ENDPOINT)
        if response.status_code == 200:
            logging.info("Successfully retrieved genesis block data")
            return response.json()
        else:
            logging.error(f"Failed to retrieve genesis block data, status code: {response.status_code}")
            raise Exception("Error fetching genesis block data")
    except Exception as e:
        logging.exception("Exception occurred while fetching genesis block")
        raise e

# Function to convert blockchain timestamp to a human-readable datetime
def convert_timestamp_to_datetime(timestamp):
    # Blockchain timestamps are usually in UNIX epoch format (seconds since 1970-01-01)
    return datetime.utcfromtimestamp(timestamp)

# Function to check how long ago the chain was created
def check_chain_creation_time():
    try:
        # Fetch the genesis block data
        genesis_block = get_genesis_block()

        # Extract the timestamp from the genesis block
        genesis_timestamp = genesis_block.get("time")
        if not genesis_timestamp:
            raise ValueError("Genesis block timestamp not found")

        # Convert the timestamp to a human-readable datetime
        chain_creation_datetime = convert_timestamp_to_datetime(genesis_timestamp)
        logging.info(f"Chain was created on: {chain_creation_datetime}")

        # Calculate how long ago the chain was created
        current_time = datetime.utcnow()
        time_since_creation = current_time - chain_creation_datetime
        logging.info(f"Chain was created {time_since_creation.days} days ago.")

        return chain_creation_datetime, time_since_creation

    except Exception as e:
        logging.error("Error occurred while checking chain creation time", exc_info=True)
        return None, None

# Example usage of the functionality
if __name__ == "__main__":
    chain_creation_datetime, time_since_creation = check_chain_creation_time()

    if chain_creation_datetime:
        print(f"Chain was created on {chain_creation_datetime}.")
        print(f"Time since creation: {time_since_creation.days} days and {time_since_creation.seconds // 3600} hours.")
    else:
        print("Unable to retrieve chain creation time.")


if __name__ == "__main__":
    main()
