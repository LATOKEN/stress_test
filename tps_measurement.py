#  continuously calculates the TPS
import time
from jsonrpcclient import request
 
LOCALNET_NODE = "http://127.0.0.1:7070"
DEVNET_NODE = "http://94.130.110.95:7070"
TESTNET_NODE = "http://95.217.17.248:7070"
 
def tps_measure():
    file = open("result.txt","w")
    latest = ''
    last_time = 0
    initial_time = 0
    total_tx = 0
    total_blocks = 0
    while True:
        cur = request(DEVNET_NODE, "eth_blockNumber").data.result
        if cur != latest:
            latest = cur
            cur_block = request(DEVNET_NODE, "eth_getBlockByNumber", latest, True).data.result
            count = len(cur_block["transactions"])
            current_time = time.time()

            if last_time > 0:
                file.write("\nBlock No: " + str(int(latest, 16)))
                file.write("\nDifference between blocks: "+str(current_time - last_time)+"sec")
                file.write("\nTx in current bloc: "+str(count))
                total_tx += count
                total_blocks += 1
            else:
                file.write("Starting...")
                initial_time = time.time()
            last_time = current_time
        
            if total_tx > 0:
                average_time = (current_time - initial_time) / total_tx
                average_block_time = (current_time - initial_time) / total_blocks
                file.write("\nTPS: "+str(1/average_time))
                file.write("\ntime/tx: "+str(average_time)+"sec")
                file.write("\navergae tx/block: "+str(total_tx / total_blocks))
                file.write("\naverage block time: "+str(average_block_time)+"sec")

            file.write("\n")
 
 
    
 
if __name__ == "__main__":
    tps_measure() 