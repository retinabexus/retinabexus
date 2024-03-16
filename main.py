#!/usr/bin/python3.9
#===========================================================================================#
#                                                                                           #
#                                 ROMULUS OBC2 MAIN PROCESS                                 #
#                                                                                           #
#===========================================================================================#
 
import subprocess, yaml
from time import sleep
from threading import Thread
from commands import ControlCenter
from obs import manageConverters
from links import uplink, downlink
from telemetry import Nano

#===========================================================================================#

# Configuration files:
with open(r'/home/pi/OBS2/inputs/config.yml') as d: config = yaml.full_load(d)
with open(r'/home/pi/OBS2/inputs/commands.yml') as d: cmdDict = yaml.full_load(d)                                                                                     

# Create the settings:
controlCenter = ControlCenter(2, cmdDict['OBC2'])

# Connect to arduino:
nano = Nano(config)
    
# Create a thread to manage converters:
convertersManager = Thread(target = manageConverters, args = (controlCenter, nano)) 
convertersManager.start()

# Start downlink :
downlink(config, controlCenter, nano)

# Start uplink:
uplink(config, controlCenter)                                                                           

# Check final command:
if controlCenter.REBOOT or controlCenter.SHUTDOWN: sleep(15)
if controlCenter.REBOOT: subprocess.run(f'sudo reboot', shell = True)
elif controlCenter.SHUTDOWN: subprocess.run('sudo shutdown', shell = True)

#===========================================================================================#
