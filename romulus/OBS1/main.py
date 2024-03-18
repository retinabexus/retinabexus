#!/usr/bin/python3.8
#===========================================================================================#
#                                                                                           #
#                                 ROMULUS OBC1 MAIN PROCESS                                 #
#                                                                                           #
#===========================================================================================#

import subprocess, yaml
from threading import Thread
from commands import ControlCenter
from time import sleep
from links import uplink, downlink
from obs import manageSubprocess

#===========================================================================================#

# Configuration files:
with open(r'C:\\Users\\Lorenzo\\Desktop\\retina_software\\OBS1\\inputs\\config.yml') as d: config = yaml.full_load(d)
with open(r'C:\\Users\\Lorenzo\\Desktop\\retina_software\\OBS1\\inputs\\commands.yml') as d: cmdDict = yaml.full_load(d)                                                                                     

# Create the settings:
controlCenter = ControlCenter(1, cmdDict['OBC1'])  

# Create a thread to manage converters:
subprocessManager = Thread(target=manageSubprocess, args = (controlCenter, config['GNSS-SDR']))  
subprocessManager.start()

# Start downlink :
downlink(config, controlCenter)
                                                                
# Start uplink:
uplink(config, controlCenter)

# Check final command:
if controlCenter.REBOOT or controlCenter.SHUTDOWN: sleep(15)
if controlCenter.REBOOT: subprocess.run(f'sudo reboot', shell = True)
elif controlCenter.SHUTDOWN: subprocess.run('sudo shutdown', shell = True)

#===========================================================================================#                                                                           

