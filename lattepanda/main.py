from threading import Thread
from obc2 import runAI, runGNSS
import yaml

if __name__ == "__main__":
    
    # Config threads
    thread_AI = Thread(target = runAI, args = ())
    thread_GNSS = Thread(target = runGNSS, args = ())
    #thread_uplink = Thread(target = uplink, args =())
    #thread_downlink = Thread(target = downlink, args = ())

    # Start threads
    thread_AI.start()
    thread_GNSS.start()
    #thread_uplink.start()
    #thread_downlink.start()

    # Join threads
    thread_AI.join()
    thread_GNSS.join()
    #thread_uplink.join()
    #thread_downlink.join()
    print("thread finished...exiting")