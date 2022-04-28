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

# change wallet password from config
wallet_password = "525bd9da919a12f7197c3961d64fd9336b3de435"

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

def get_random_hex_message(len):
    len = len * 2
    msg = "0x"
    for x in range(len):
        digit = hex(random.randint(0,15))
        msg = msg + digit[2]
    return msg

def sign_message(message, use_new_chain_id):
    return send_api_request([message, use_new_chain_id], "fe_signMessage")
    
def verify_signed_message(message, signed_message, use_new_chain_id):
    return send_api_request([message, signed_message, use_new_chain_id], "fe_verifySign")

def sign_and_verify_random_message(use_new_chain_id):
    msg = get_random_hex_message(random.randint(64,111))
    signed_message = sign_message(msg, use_new_chain_id)
    result = verify_signed_message(msg, signed_message, use_new_chain_id)
    if result == True:
        print("signature verified")
    else:
        print("signature not verified")

def unlock_wallet():
    return send_api_request([wallet_password, 1], "fe_unlock")

if __name__ == "__main__":
    # Current chain id issue is related to recover id, it always gets 0.
    # But it could be 0 or 1 in our case ( 0 to 3 in general )
    # So sometimes the recover id matched and sometimes don't
    no_of_test = 100 
    for _ in range(no_of_test):
        unlocked = unlock_wallet()
        print(unlocked)
        if (unlocked == "incorrect_password"):
            continue
        sign_and_verify_random_message(True)
        sign_and_verify_random_message(False)