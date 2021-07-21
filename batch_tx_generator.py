import asyncio
import os
import time
import web3
from jsonrpcclient import request
from ethereum import utils

LOCALNET_NODE = "http://127.0.0.1:7070"
FEED_PRIVATE_KEY = bytes.fromhex("d95d6db65f3e2223703c5d8e205d98e3e6b470f067b0f94f6c6bf73d4301ce48")
CHAIN_ID = 41
WALLETS_NUMBER = 8
SEND_CYCLES = 10
ITERATION = 3

def current_block_number():
    return int(request(LOCALNET_NODE, "eth_blockNumber").data.result, 16)

def get_balance(address):
    return request(LOCALNET_NODE, "fe_getBalance", address).data.result

def block_tx_hash(block_number):
    block = request(LOCALNET_NODE, "eth_getBlockByNumber", hex(block_number), True).data.result
    return [tx["hash"] for tx in block["transactions"]]


class Wallet: 
    
    def __init__(self, private_key, url):
        self.url = url 
        self.private_key = private_key 
        self.address = utils.checksum_encode(utils.privtoaddr(self.private_key))
        self.nonce = request(self.url, "eth_getTransactionCount", self.address, "latest").data.result 

    def sign_tx(self, transaction):
        return web3.eth.Account.signTransaction(transaction, self.private_key)        


class TxManager: 
    
    def __init__(self):
        self.tx_batches = {}
        self.start = current_block_number() 

    def __create_tx(self, wallet, to_address, amount):
        
        transaction = {
            "from": wallet.address,
            "to": to_address,
            "value": amount,
            "gas": 200000000,
            "gasPrice": 234567897,
            "nonce": wallet.nonce,
            "chainId": CHAIN_ID
        }
        wallet.nonce += 1 

        signed_tx = wallet.sign_tx(transaction) 
        return web3.Web3.toHex(signed_tx.rawTransaction)
        
    def __check_finality(self, tx_hash_list):
        
        print("all transaction hashes: ")
        print(tx_hash_list)
        print("")
        
        tx_hash_set = set(tx_hash_list)

        while len(tx_hash_set) > 0:
            if current_block_number() >= self.start:
                tset = tx_hash_set.intersection(block_tx_hash(self.start))
                for t in tset:
                    print(t + " in block " + str(self.start))
                tx_hash_set.difference_update(tset) 
                self.start += 1

    def instant_send(self, wallet, to_address, amount):
        raw_tx = self.__create_tx(wallet, to_address, amount)
        return request(wallet.url, "eth_sendRawTransaction", raw_tx).data.result

    def send_each_other(self, wallets,  amount):
        for i in range(len(wallets) - 1):
            self.add_to_batch(wallets[i], wallets[i + 1].address, amount)
        self.add_to_batch(wallets[-1], wallets[0].address, amount)
    
    def add_to_batch(self, wallet, to_address, amount):
        raw_tx = self.__create_tx(wallet, to_address, amount)
        if wallet.url in self.tx_batches:
            self.tx_batches[wallet.url].append(raw_tx)
        else:
            self.tx_batches[wallet.url] = [raw_tx]
        
        return raw_tx 
    
    async def __task(self, url, tx_batch, tx_hash_list):
        tx_hash_list.extend(request(url, "la_sendRawTransactionBatch", tx_batch).data.result)

    async def execute_batch(self, check_finality = False):
        tx_hash_list = []
        tasks = [] 
        for url in self.tx_batches:
            tx_batch = self.tx_batches[url]
            tasks.append(asyncio.create_task(self.__task(url, tx_batch, tx_hash_list)))
        
        for t in tasks:
            await t 
        
        self.tx_batches.clear()
        if check_finality == True: 
            self.__check_finality(tx_hash_list)
        
        self.start = current_block_number()


def print_balance(feed_wallet, wallets):

    print("\nfeed balance: ")
    print(get_balance(feed_wallet.address))

    print("\nother wallets' balance: ")
    for wallet in wallets: 
        balance = get_balance(wallet.address) 
        print(balance)

    print("\n")


def print_address(feed_wallet, wallets):

    print("\nfeed wallet address:")
    print(feed_wallet.address)
    
    print("\nother wallets' address:")
    for w in wallets:
        print(w.address)

    print("\n")


async def main():

    print("Start setup...")

    tx_manager = TxManager()
    urls = ["http://127.0.0.1:7070", "http://127.0.0.1:7071", "http://127.0.0.1:7072", "http://127.0.0.1:7073"]

    feed_wallet = Wallet(FEED_PRIVATE_KEY, urls[0])
    wallets = [Wallet(utils.sha3(os.urandom(4096)), urls[_%len(urls)]) for _ in range(WALLETS_NUMBER)]
    print_address(feed_wallet, wallets)
    
    for w in wallets:
        tx_manager.instant_send(feed_wallet, w.address, 1000000000000000000)
    time.sleep(10) 
    print_balance(feed_wallet, wallets)

    print("Start sending txes...")
    start = time.time() 

    for iter in range(ITERATION):

        print("iteration: " + str(iter))

        for i in range(SEND_CYCLES):
            tx_manager.send_each_other(wallets, 1000)

        await tx_manager.execute_batch(True)
        print_balance(feed_wallet, wallets)


    end = time.time()

    print("{} secs elapsed, {} txes are sent,  send TPS is {}".format(end - start, SEND_CYCLES * WALLETS_NUMBER * ITERATION,
                                                                      (SEND_CYCLES * WALLETS_NUMBER * ITERATION) / (end - start)))


if __name__ == "__main__":
    asyncio.run(main())