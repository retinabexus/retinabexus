from threading import Thread
import time

def experiment():

    while True:
        print("I'm performing the first experiment\n")
        time.sleep(1)

def uplink():


    print("I'm receiving telecommands\n")
    time.sleep(1)

def downlink():

    while True:
        print("I'm sending packets\n")
        time.sleep(1)

if __name__ == "__main__":
    exp = Thread(target=experiment)
    upl = Thread(target=uplink)
    dow = Thread(target=downlink)

    exp.start()
    upl.start()
    dow.start()

        

