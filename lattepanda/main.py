from threading import Thread
from obc2 import runAI, runGNSS
from telecommands import uplink
import yaml
import serial
from utils_AI  import*


if __name__ == "__main__":

    # Link uart
    serd = serial.Serial(baudrate = 115200, port = '/dev/linkusb')
    
    # Read configuration file
    with open('/home/retina/Desktop/retinabexus/lattepanda/Input/config.yaml','r') as d: config = yaml.full_load(d)
    # Read commands file
    with open('/home/retina/Desktop/retinabexus/lattepanda/Input/commands.yaml','r') as d: commands = yaml.full_load(d)

    # Config threads
    gnss   = Thread(target = runGNSS, args = (config, commands))
    ai     = Thread(target = runAI, args = (config, commands))
    listen = Thread(target = uplink, args = (serd, config))

    # Start threads
    gnss.start()
    ai.start()
    listen.start()

    # Join threads
    gnss.join()
    ai.join()
    listen.join()

    print("thread finished...exiting")