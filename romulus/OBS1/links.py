import socket, os, csv
from threading import Thread

from commands import ControlCenter

from time import sleep
from obs import receiveCommands, sendGnssSdr

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
                print(f"\n *** Connected to TCP server: {addr}...\n")
            except socket.error as error:
                print(f"\n *** While connecting to the server something went wrong:")
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

def downlink(config: dict, controlCenter: ControlCenter):
    """
    Function to handle the downlink with the GS.

        Args: 
        - Configuration dictionary
        - Object of the class ControlCenter
    """

    # Create the internal loop server
    internalAddr = ('127.0.0.1', config['SOCKET']['PORT_GNSS-SDR'])
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 

    # Bind the server to an IP and port:
    binded = False
    while not binded:
        try:
            # Bind the server to an IP address and port:
            server.bind(internalAddr)    
            print(f"\n *** UDP internal loop server binded on {internalAddr}")
        except socket.error as error:
            print(f"\n *** Cannot bind the UDP internal loop server on {internalAddr}:")
            print(f" *** {error}")
            print(f" *** Trying to bind again...")
            sleep(5)
        else: binded = True
    
    # Create the socket client:
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
 
    # Create a thread to send telemetry:
    gnssSdrSender = Thread(target = sendGnssSdr, args = (server, client, config, controlCenter))
    # Start threading:
    gnssSdrSender.start() 

################################################################################################################