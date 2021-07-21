# continuously prints transactions of every latest block

from jsonrpcclient import request

LOCALNET_NODE = "http://127.0.0.1:7070"
DEVNET_NODE = "http://88.99.87.58:7070"
TESTNET_NODE = "http://95.217.17.248:7070"

def tx_watcher():
    latest = ''
    while True:
        cur = request(LOCALNET_NODE, "eth_blockNumber").data.result
        if cur != latest:
            latest = cur
            print("Block No: " + str(int(latest, 16)))
            cur_block = request(LOCALNET_NODE, "eth_getBlockByNumber", latest, True).data.result
            txs = cur_block["transactions"]
            for tx in txs:
                print("tx hash: " + tx["hash"] + " from: " + tx["from"] + " to: " + tx["to"]) 
    

if __name__ == "__main__":
    tx_watcher() 