import asyncio
import os
import time
import web3
from jsonrpcclient import request
from ethereum import utils

LOCALNET_NODE = "http://127.0.0.1:7070"
FEED_PRIVATE_KEY = bytes.fromhex('d95d6db65f3e2223703c5d8e205d98e3e6b470f067b0f94f6c6bf73d4301ce48')
CHAIN_ID = 41
WALLETS_NUMBER = 10
SEND_CYCLES = 10

g_txes = []
tx_batch = []


class Connections:
    def __init__(self, hosts):
        self.connections = []
        for host in hosts:
            self.connections.append(web3.Web3(web3.Web3.HTTPProvider(host)))
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if len(self.connections) == 0:
            raise StopIteration
        self.index += 1
        if self.index >= len(self.connections):
            self.index = 0
        return self.connections[self.index]


class Wallet:
    def __init__(self, private_key, connection):
        self.private_key = private_key
        self.address = utils.checksum_encode(utils.privtoaddr(self.private_key))
        self.connection = connection
        self.nonce = self.connection.eth.getTransactionCount(self.address)

    def send(self, to, amount):
        transaction = {
            'from': self.address,
            'to': to,
            'value': amount,
            'gas': 200000000,
            'gasPrice': 234567897,
            'nonce': self.nonce,
            'chainId': CHAIN_ID
        }
        signed = web3.eth.Account.signTransaction(transaction, self.private_key)
        tx_batch.append(web3.Web3.toHex(signed.rawTransaction))
        self.nonce += 1


async def send_each_other(wallets,  amount):
    for i in range(len(wallets) - 1):
        wallets[i].send(wallets[i + 1].address, amount)
        wallets[-1].send(wallets[0].address, amount)


async def main():
    c = Connections(['http://127.0.0.1:7070',
                     'http://127.0.0.1:7071',
                     'http://127.0.0.1:7072',
                     'http://127.0.0.1:7073'])
    feed_wallet = Wallet(FEED_PRIVATE_KEY, next(c))
    wallets = [Wallet(utils.sha3(os.urandom(4096)), next(c)) for _ in range(WALLETS_NUMBER)]
    for w in wallets:
        feed_wallet.send(w.address, 1000000000)

    request(LOCALNET_NODE, 'la_sendRawTransactionBatch', tx_batch)

    print("Start sending txes...")

    start = time.time()
    tasks = []
    for i in range(SEND_CYCLES):
        tasks.append(asyncio.create_task(send_each_other(wallets, 1000)))

    for t in tasks:
        await t

    g_txes = request(LOCALNET_NODE, 'la_sendRawTransactionBatch', tx_batch).data.result 
    
    end = time.time()

    print("{} secs elapsed, {} txes are sent,  send TPS is {}".format(end - start, SEND_CYCLES * WALLETS_NUMBER,
                                                                      (SEND_CYCLES * WALLETS_NUMBER) / (end - start)))


if __name__ == '__main__':
    asyncio.run(main())