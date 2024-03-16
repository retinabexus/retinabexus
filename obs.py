import select, subprocess, os, csv
import RPi.GPIO as GPIO

from socket import socket
from datetime import datetime
from threading import Lock
from time import sleep

from commands import ControlCenter, FeedbackPacket, isCommandPacket
from telemetry import Nano, Raspy, TelemetryPacket
from pvt import Piksi, PiksiPacket

from gpiozero import CPUTemperature

from utils import writeCSV


####################################################################################################

def sendTelemetry(client: socket, clientLock: Lock, nano: Nano, raspy: Raspy, config: dict, controlCenter: ControlCenter):
    """
    Function to read Arduino data and to send them via UDP.

        Args: 
        - Socket UDP client
        - Shared lock to receive in a thread-safe way
        - Object of the class Nano
        - Object of the class Raspy
        - Configuration dictionary
        - Object of the class ControlCenter
    """

    # Configuration:
    addr = (config['SOCKET']['IP_GS'], config['SOCKET'][f'PORT_GS'])
    sleeptime = config['PACKETS']['TELEMETRY']['SLEEPTIME']
    expID = config['PACKETS']['TELEMETRY']['EXPERIMENT_ID']
    pktID = config['PACKETS']['TELEMETRY']['PACKET_ID']
    path = config['PACKETS']['TELEMETRY']['ABS_PATH']
    fieldnames = config['PACKETS']['TELEMETRY']['FIELDNAMES']
    
    # Number of length of each file
    maxRows = int(config['PACKETS']['TELEMETRY']['FILE_LENGTH']/sleeptime)

    # Create new file:
    files = [f for f in sorted(os.listdir(path)) if 'telemetry' in f]
    if len(files) == 0: fileN = 0
    else:
        lastFile = files[-1]
        fileN    = int(lastFile.replace('telemetry_','').replace('.csv','')) + 1
    filename = path + 'telemetry_%2.2i'%int(fileN) + '.csv'
    with open(filename, 'w') as telemetryFile: csv.writer(telemetryFile).writerow(fieldnames)

    # Initialize cpu object
    cpu = CPUTemperature()

    # Initialize the dataclass object:
    pktNumber = 0
    packet = TelemetryPacket()
    packet.experiment = expID
    packet.type = pktID

    # Main loop:
    while not (controlCenter.SHUTDOWN or controlCenter.REBOOT):
        # Sleep:
        sleep(sleeptime)
        # Build the packet:
        pktNumber += 1
        packet.number = pktNumber
        # Add arduino data:
        packet = nano.buildPacket(packet)
        # Add raspberry data:
        packet = raspy.buildPacket(packet)
        # Add current datetime in UTC:
        packet.date = datetime.utcnow()
        # Add cpu temperature
        try: packet.cpu_temp = str(cpu.temperature)
        except Exception as error:
            packet.cpu_temp = '-273.16'
            print(f" *** While reading CPU temperature something went wrong:") 
            print(f" *** {error}\n")     
        # Check update file:
        if (pktNumber%maxRows) == 0:
            fileN  += 1
            filename = path + 'telemetry_%2.2i'%int(fileN) + '.csv'
            with open(filename, 'w') as telemetryFile: csv.writer(telemetryFile).writerow(fieldnames)
        # Refresh?
        if not os.path.exists(filename):
            pktNumber = 1
            packet.number = pktNumber
            fileN = 0 
            filename = path + 'telemetry_%2.2i'%int(fileN) + '.csv'
            with open(filename, 'w') as telemetryFile: csv.writer(telemetryFile).writerow(fieldnames)
        # Save the packet:
        writeCSV(repr(packet).split(","), filename, fieldnames)
        # String message:
        pkt = repr(packet).encode('utf-8')
        # Send the packet:
        try: 
            with clientLock: client.sendto(pkt, addr)
        except Exception as error:
            print(f" *** While sending telemetry packet something went wrong:") 
            print(f" *** {error}\n")
    print(" *** Stopping the thread which sends telemetry...\n")
    sleep(3)
    
    # Close serial communication
    nano.close()
    
    # Close UDP connection:
    print(f" *** Closing UDP client...\n")
    with clientLock: client.close()

####################################################################################################

def sendPVT(client: socket, clientLock: Lock, piksi: Piksi, config: dict, controlCenter: ControlCenter):
    """
    Function to read Piksi data and to send them via UDP.

        Args: 
        - Socket UDP client
        - Shared lock to receive in a thread-safe way
        - Object of the class Piksi
        - Configuration dictionary
        - Object of the class ControlCenter
    """

    # Configuration:
    obcNumber = controlCenter.obcNumber
    addr = (config['SOCKET']['IP_GS'], config['SOCKET']['PORT_GS'])
    sleeptime = config['PACKETS']['PVT']['SLEEPTIME']
    expID = config['PACKETS']['PVT']['EXPERIMENT_ID']
    pktID = config['PACKETS']['PVT']['PACKET_ID']
    path = config['PACKETS']['PVT']['ABS_PATH']
    fieldnames = config['PACKETS']['PVT']['FIELDNAMES']

    # Number of length of each file
    maxRows = int(config['PACKETS']['PVT']['FILE_LENGTH']/sleeptime)

    # Create new file:
    files = [f for f in sorted(os.listdir(path)) if 'pvt' in f]
    if len(files) == 0: fileN = 0
    else:
        lastFile = files[-1]
        fileN    = int(lastFile.replace('pvt_','').replace('.csv','')) + 1
    filename = path + 'pvt_%2.2i'%int(fileN) + '.csv'
    with open(filename, 'w') as pvtFile: csv.writer(pvtFile).writerow(fieldnames)

    # Initialize the dataclass object:
    previousDate = str(datetime.now())
    pktNumber = 0
    packet = PiksiPacket()
    packet.experiment = expID
    packet.type = pktID
    
    # Main loop:
    while not (controlCenter.SHUTDOWN or controlCenter.REBOOT):
        # Sleep:
        sleep(sleeptime)
        # Build the packet:
        pktNumber += 1
        packet.number = pktNumber
        # Read piksi data:
        packet = piksi.buildPacket(packet)   
        # Check date update:
        if controlCenter.cmdDict[f'SET_TIME_OBC{obcNumber}']['STATUS']:
            try: 
                # Set date:
                subprocess.run(f"sudo date -s '{packet.date}'", shell = True, stdout=subprocess.PIPE, text = True)
            except Exception as error:
                print(' *** While setting the raspbserry date something went wrong:')
                print(f" *** {error}\n")
            else: 
                # Reboot the command status:
                controlCenter.switchCommand(f"SET_TIME_OBC{obcNumber}", 0)
        # Check update file:
        if (pktNumber%maxRows) == 0:
            fileN  += 1
            filename = path + 'pvt_%2.2i'%int(fileN) + '.csv'
            with open(filename, 'w') as pvtFile: csv.writer(pvtFile).writerow(fieldnames)
        # Refresh?
        if not os.path.exists(filename):
            pktNumber = 1
            packet.number = pktNumber 
            fileN = 0 
            filename = path + 'pvt_%2.2i'%int(fileN) + '.csv'
            with open(filename, 'w') as pvtFile: csv.writer(pvtFile).writerow(fieldnames)      
        # Save the packet:
        writeCSV(repr(packet).split(","), filename, fieldnames)  
        # String message:
        pkt = repr(packet).encode('utf-8')
        # Send the packet:
        if previousDate != str(packet.date):
            try: 
                with clientLock: client.sendto(pkt, addr)
            except Exception as error:
                print(f" *** While sending PVT packet something went wrong:") 
                print(f" *** {error}\n")
            else: previousDate = str(packet.date)
    print("\n *** Stopping the thread which sends PVT...\n")
    

####################################################################################################

def receiveCommands(client: socket, config: dict, controlCenter: ControlCenter):
    """
    Function to receive telecommands via TCP and change commands status.

        Args: 
        - Socket TCP client
        - Configuration dictionary
        - Object of the class ControlCenter
    """

    # Configuration:
    obcNumber = controlCenter.obcNumber
    timeout = config['PACKETS']['COMMANDS']['TIMEOUT']
    buffersize = config['PACKETS']['COMMANDS']['BUFFERSIZE']
    length = config['PACKETS']['COMMANDS']['DATA_LENGTH']
    filename = config['PACKETS']['COMMANDS']['FILENAME']
    fieldnames = config['PACKETS']['COMMANDS']['FIELDNAMES']

    # Initialize the dataclass object (feedback packet):
    feedback = FeedbackPacket()
    feedback.experiment = config['PACKETS']['FEEDBACKS']['EXPERIMENT_ID']
    feedback.type = config['PACKETS']['FEEDBACKS']['PACKET_ID']
    
    # Main loop:
    while not (controlCenter.SHUTDOWN or controlCenter.REBOOT or controlCenter.REBOOT_TCP):
        # Listen for new inputs:
        ready, _, _ = select.select([client], [], [], timeout)
        try:
            if ready: 
                # Receive the packet:
                packet = client.recv(buffersize)
                packet = packet.decode('utf-8').lstrip().rstrip()
                # Check if the command is the null string:
                if packet == '':
                    # Check if the connection is still alive:
                    client.send(b'0')
                # Check if the command is a keepalive:
                elif packet != '0':
                    # Split the message:
                    packet = packet.split(",")
                    # Check if it is a command packet:
                    if isCommandPacket(packet, config):
                        # Extract the command:
                        cmd = packet[length - 1]
                        print(f' *** RECEIVED: {cmd}\n')
                        # Refresh?
                        if not os.path.exists(filename):
                            with open(filename, 'w') as commandsFile: csv.writer(commandsFile).writerow(fieldnames)
                        # Save the packet:
                        writeCSV(packet, filename, fieldnames)
                        # Switch the command:
                        controlCenter.switchCommand(cmd, 1)
                        # Build the packet:
                        feedback.number += 1
                        # Add the command:
                        feedback.fdb = controlCenter.newCmd
                        # Add current datetime in UTC:
                        feedback.date = datetime.utcnow()
                        client.send(repr(feedback).encode('utf-8'))
                # If the command is a keepalive send a zero in return:
                else: client.send(b'0')
            else:
                # Check if the connection is still alive:
                client.send(b'0')
        except Exception as error:
            if not controlCenter.SHUTDOWN or controlCenter.REBOOT:
                print(f" *** Broken TCP connection:") 
                print(f" *** {error}")
                print(" *** Trying to restore it...\n")
                # Turn-on the resetTCP command:
                controlCenter.switchCommand(f"REBOOT_TCP_OBC{obcNumber}", 1)
                # Break the loop:
                break
    print(" *** Stopping the thread which receives telecommands...\n")

####################################################################################################

def manageConverters(controlCenter: ControlCenter, nano: Nano):
    """
    Function to manage converters.

        Args: 
        - Object of the class ControlCenter
        - Object of the class Nano
    """

    # Set channel mode:
    GPIO.setmode(GPIO.BCM) 
    
    # Configure converters:
    for g in [controlCenter.cmdDict['PATCH_ON']['CHANNEL'], controlCenter.cmdDict['PIKSI_ON']['CHANNEL']]: 
        GPIO.setup(g, GPIO.OUT)
    GPIO.output(controlCenter.cmdDict['PATCH_ON']['CHANNEL'], GPIO.LOW)
    GPIO.output(controlCenter.cmdDict['PIKSI_ON']['CHANNEL'], GPIO.HIGH)

    # Main loop:
    while not (controlCenter.SHUTDOWN or controlCenter.REBOOT):
        # Waits for new commands:
        controlCenter.newCmdEvent.wait()
        # Check if a refresh of the file is needed:
        if controlCenter.newCmd == 'DELETE_FILES_OBC2': os.system(f'rm /home/pi/OBS2/outputs/*')
        # Check if the command requires Raspberry converters management:
        manageGPIO, channel = controlCenter.cmdToChannel(controlCenter.newCmd)
        if manageGPIO:
            # Manage converter:
            print(f' *** Managing converter on channel {channel}...\n')
            try:
                if 'ON' in controlCenter.newCmd: GPIO.output(channel, GPIO.HIGH)
                else: GPIO.output(channel, GPIO.LOW)
            except Exception as error:
                print(f"\n *** While managing converters something went wrong:") 
                print(f" *** {error}\n")
        # Check if the command requires Arduino converters management:
        elif (any(status in controlCenter.newCmd for status in ('ON','OFF'))) and (any(dev in controlCenter.newCmd for dev in ('OBC1','OBC2'))):
            # Send command to arduino:
            nano.serialWrite(controlCenter.newCmd)
        # Clear the event:
        with controlCenter.cmdLock: controlCenter.newCmdEvent.clear()
        # Reset the status of the command:
        if not any(status in controlCenter.newCmd for status in ('REBOOT','SHUTDOWN')):
            controlCenter.switchCommand(controlCenter.newCmd, 0)
    print(" *** Stopping the thread which manage converters...\n")
    GPIO.cleanup()

####################################################################################################
