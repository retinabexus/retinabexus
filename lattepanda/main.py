from threading import Thread
from obc2 import runAI, runGNSS, runGNSS2
import yaml
import multiprocessing

if __name__ == "__main__":
    
    # Config threads
    gnss   = Thread(target = runGNSS, args = ())
    ai     = Thread(target = runAI, args = ())
    #uplink = Thread(target = uplink, args =())
    #thread_downlink = Thread(target = downlink, args = ())

    # Start threads
    gnss.start()
    ai.start()
    #uplink.start()
    #thread_downlink.start()

    # Join threads
    gnss.join()
    ai.join()

    #thread_uplink.join()
    #thread_downlink.join()
    print("thread finished...exiting")