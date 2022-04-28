from ast import Return
from sys import api_version
from eth_keys.datatypes import PublicKey
from eth_utils.address import to_checksum_address
from requests.models import Response
import web3
from eth_keys import keys
import eth_utils
from eth_utils import decode_hex
from jsonrpcclient import request
import requests
import time
import ethereum
import random

LOCALNET_NODE = "http://localhost:7070"

#set chain id from config
old_chain_id = 25
new_chain_id = 227
session = requests.Session()
def send_api_request_to_address(address, params , method):
    payload= {"jsonrpc":"2.0",
           "method":method,
           "params":params,
           "id":0}
    
    headers = {'Content-type': 'application/json'}
    response = session.post(address, json=payload, headers=headers)
    try:
        res = response.json()['result']
        return res
    except Exception as eer:
        print(response.json())
        print("exception: " + format(eer))
        return eer

def send_api_request(params , method):
    return send_api_request_to_address(LOCALNET_NODE, params, method)

def update_nonce(address):
    method = "eth_getTransactionCount"
    params = [
        address,
        "latest"
    ]
    nonce = send_api_request(params , method)
    int_nonce = int(nonce,16)
    params = [
        address,
        "pending"
    ]
    nonce = send_api_request(params , method)
    int_nonce = max(int_nonce , int(nonce,16))
    return int_nonce

def generate_random_private_key():
    key = "0x"
    for _ in range(64):
        digit = hex(random.randint(0,15))
        key = key + digit[2]
    key_bytes = decode_hex(key)
    return keys.PrivateKey(key_bytes)

def generate_random_address():
    key = "0x"
    for _ in range(40):
        digit = hex(random.randint(0,15))
        key = key + digit[2]
    return ethereum.utils.checksum_encode(key)

def generate_tx(from_address, to_address, amount, chain_id):
    int_nonce = update_nonce(from_address)
    transaction = {
        "from": from_address,
        "to": to_address,
        "value": amount,
        "gas": 100000000,
        "gasPrice": 1,
        "nonce": int_nonce,
        "chainId": chain_id
    }
    return transaction

def verify_raw_tx(raw_tx, use_new_chain_id):
    return send_api_request([raw_tx, use_new_chain_id], "fe_verifyRawTransaction")

def test_random_tx(my_private_key, chain_id, use_new_chain_id):
    to_address = generate_random_address()
    amount = random.randint(0,100000)
    my_address = my_private_key.public_key.to_checksum_address()
    tx = generate_tx(my_address, to_address, amount, chain_id)
    print(tx)
    signed_tx = web3.eth.Account.signTransaction(tx, my_private_key.to_bytes())
    raw_tx = web3.Web3.toHex(signed_tx.rawTransaction)
    tx_hash = verify_raw_tx(raw_tx, use_new_chain_id)
    print(tx_hash)
    
def start_test():
    my_private_key = generate_random_private_key()
    no_of_test = 10
    for _ in range(no_of_test):
        test_random_tx(my_private_key, old_chain_id, False)
        test_random_tx(my_private_key, new_chain_id, True)

if __name__ == "__main__":
    no_of_test = 10
    for _ in range(no_of_test):
        start_test()
        