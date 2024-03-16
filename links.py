import socket, os, csv
from threading import Thread, Lock
from time import sleep

from commands import ControlCenter
from telemetry import Nano, Raspy
from pvt import Piksi

from obs import sendTelemetry, receiveCommands
from obs import sendPVT

################################################################################################################

def uplink(config: dict, controlCenter: ControlCenter):
    """
    Function to handle the uplink with the GS.

        Args: 
        - Configuration dictionary
        - Object of the class ControlCenter
    """

    # Configuration:
    obcNumber = controlCenter.obcNumber
    IP = config['SOCKET'][f'IP_GS']
    port = config['SOCKET'][f'PORT_GS']
    cmdFilename = config['PACKETS']['COMMANDS'][f'FILENAME']
    cmdFieldnames = config['PACKETS']['COMMANDS']['FIELDNAMES']
    addr = (IP, port)                   

    # Refresh the commands database:
    if not os.path.exists(cmdFilename):
        with open(cmdFilename, 'w') as commandsFile: csv.writer(commandsFile).writerow(cmdFieldnames)

    # Handle TCP connection:
    while not (controlCenter.SHUTDOWN or controlCenter.REBOOT):
        # Establish connection:
        connected = False
        while not connected:
            try:
                # Create the socket client:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
                # Connect to server:
                client.connect(addr)
                print(f" *** Connected to TCP server: {addr}...\n")
            except socket.error as error:
                print(f" *** While connecting to the server something went wrong:")
                print(f" *** {error}")
                print(f" *** Trying to connect again to {addr}...\n")
                sleep(5)
                # Close socket client:
                print(f" *** Closing TCP client...\n")
                client.close()
            else: connected = True
        # Create a thread to receive commands:
        cmdReceiver = Thread(target = receiveCommands, args = (client, config, controlCenter)) 
        # Start threading:
        cmdReceiver.start()  
        # Join threading:
        cmdReceiver.join()
        # Close socket client:
        print(f" *** Closing TCP client...\n")
        client.close()
        # Restore connection status:
        if controlCenter.REBOOT_TCP: controlCenter.switchCommand(f"REBOOT_TCP_OBC{obcNumber}", 0)

################################################################################################################

def downlink(config: dict, controlCenter: ControlCenter, nano: Nano):
    """
    Function to handle the downlink with the GS.

        Args: 
        - Configuration dictionary
        - Object of the class ControlCenter
        - Object of the class Nano
    """      

    # Create the socket client:
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
    # Create the lock to send in a thread-safe way:
    clientLock = Lock()    
    # Create raspberry interface:
    raspy = Raspy(config)
    # Create piksi interface:
    piksi = Piksi(config) 
    # Create a thread to send telemetry:
    telSender = Thread(target = sendTelemetry, args = (client, clientLock, nano, raspy, config, controlCenter))
    # Create a thread to send telemetry:
    pvtSender = Thread(target = sendPVT, args = (client, clientLock, piksi, config, controlCenter))
    # Start threading:
    telSender.start() 
    pvtSender.start()

################################################################################################################