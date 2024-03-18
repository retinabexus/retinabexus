import select, subprocess, os, csv, shlex

from socket import socket
from datetime import datetime

import inputs.gnss_synchro_pb2 as Gnss_Synchro
import codecs
import google.protobuf.pyext
from time import sleep
from pyspectator.processor import Cpu

from commands import ControlCenter, FeedbackPacket, isCommandPacket
from utils import writeCSV


####################################################################################################

def sendGnssSdr(server: socket, client: socket, config: dict, controlCenter: ControlCenter):
    """
    Function to read Piksi data and to send them via UDP.

        Args: 
        - Socket UDP internal loop server
        - Socket UDP client
        - Configuration dictionary
        - Object of the class ControlCenter
    """
    
    # Configuration:
    addr = (config['SOCKET']['IP_GS'], config['SOCKET']['PORT_GS'])
    sleeptime = config['PACKETS']['GNSS-SDR']['SLEEPTIME']
    timeout = config['PACKETS']['GNSS-SDR']['TIMEOUT']
    buffersize = config['PACKETS']['GNSS-SDR']['BUFFERSIZE']
    expID = config['PACKETS']['GNSS-SDR']['EXPERIMENT_ID']
    pktID = config['PACKETS']['GNSS-SDR']['PACKET_ID']
    path = config['PACKETS']['GNSS-SDR']['ABS_PATH']
    fieldnames = config['PACKETS']['GNSS-SDR']['FIELDNAMES']
    sendProcessed = config['PACKETS']['GNSS-SDR']['SEND_PROCESSED']

    # Number of length of each file
    maxRows = int(config['PACKETS']['GNSS-SDR']['FILE_LENGTH']/sleeptime)

    # Create new file:
    files = [f for f in sorted(os.listdir(path)) if 'gnss_sdr' in f]
    if len(files) == 0: fileN = 0
    else:
        lastFile = files[-1]
        fileN    = int(lastFile.replace('gnss_sdr_','').replace('.csv','')) + 1
    filename = path + 'gnss_sdr_%2.2i'%int(fileN) + '.csv'
    with open(filename, 'w') as gnssSdrFile: csv.writer(gnssSdrFile).writerow(fieldnames)
    
    # Gnss-Sdr observables config
    pktNumber = 0
    gnss_observables = Gnss_Synchro.Observables()
    
    # Main loop:
    while not (controlCenter.SHUTDOWN or controlCenter.REBOOT):
        # Sleep:
        sleep(sleeptime)
        # Initialize new dictionary:
        packetDict = {field: 'None' for field in fieldnames}
        # Update packet number:
        pktNumber += 1
        # Send processed data:
        if sendProcessed:
            # Listen for new inputs: 
            ready, _, _ = select.select([server], [], [], timeout)
            if ready:
                try:
                    # Receive the packet:
                    packet, _ = server.recvfrom(buffersize)
                    # Decode the packet:
                    gnss_observables.ParseFromString(packet)
                    # Extract the packet if contains pseudorange value:
                    packet = str(gnss_observables.observable[0]).rstrip().lstrip().split("\n") 
                    # Extract received fields and values:
                    rcvdFields = [data.split(":")[0] for data in packet]
                    rcvdValues = [data.split(":")[1] for data in packet]
                    # Check pseudorange:
                    if "pseudorange_m" not in rcvdFields: continue
                    # Add channel ID if not present:
                    if "channel_id" not in rcvdFields:
                        rcvdFields.append("channel_id")
                        rcvdValues.append('0')
                    # Split new data
                    for field, value in zip(rcvdFields, rcvdValues):
                        if field in fieldnames: packetDict[field] = value.rstrip().lstrip()
                except Exception as error:
                    print(f" *** While building GNSS-SDR processed data something went wrong:") 
                    print(f" *** {error}\n")
        # Refresh?
        if not os.path.exists(filename):
            pktNumber = 1
            fileN = 0 
            filename = path + 'gnss_sdr_%2.2i'%int(fileN) + '.csv'
            with open(filename, 'w') as gnssSdrFile: csv.writer(gnssSdrFile).writerow(fieldnames) 
        # Add standard fields:
        packetDict['ID'] = expID
        packetDict['Type']  = pktID
        packetDict['Number'] = str(pktNumber)  
        packetDict['Date'] = str(datetime.utcnow())
        # Add the CPU temperature:
        try: cpuTemp = Cpu(monitoring_latency = 1).temperature
        except Exception as error: 
            cpuTemp = -273.16
            print(f" *** While taking cpu temperature something went wrong:") 
            print(f" *** {error}\n")
        packetDict['cpu_temp'] = str(cpuTemp)
        # Build the string to be sent:
        msg = ""
        for field in fieldnames: msg += packetDict[field] + ","
        msg = msg[:-1]
        # Check update file:
        if (pktNumber%maxRows) == 0:
            fileN  += 1
            filename = path + 'gnss_sdr_%2.2i'%int(fileN) + '.csv'
            with open(filename, 'w') as gnssSdrFile: csv.writer(gnssSdrFile).writerow(fieldnames) 
        # Save the packet:
        writeCSV(msg.split(","), filename, fieldnames)  
        # Send the packet:
        try: client.sendto(msg.encode('utf-8'), addr)
        except Exception as error:
            print(f" *** While sending GNSS-SDR packet something went wrong:") 
            print(f" *** {error}\n")
            
    print("\n *** Stopping the thread which sends GNSS-SDR packets...\n")
    
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
    filename = config['PACKETS']['COMMANDS'][f'FILENAME']
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

def manageSubprocess(controlCenter: ControlCenter, processDict: dict):
    """
    Function to manage converters.

        Args: 
        - Object of the class ControlCenter
        - Gnss-sdr process dictionary
    """
    
    def killGnssSdrProcess(processDict: dict):
        """
        Function to kill gnss-sdr process
        """    
        # Find gnss-sdr PID:  
        p = subprocess.Popen('pidof gnss-sdr', shell = True, stdout=subprocess.PIPE, text=True)
        PID, _= p.communicate()
        PID = PID.rstrip("\n")
        # Kill the process:
        if len(PID) > 0:
            #os.system(f'sudo kill -9 {PID}')
            os.system(f'sudo killall -9 gnss-sdr')
            print('\n *** Process killed!\n')
        # Restore enabled flag:
        for key in processDict.keys():
            if processDict[key]['ENABLED']: processDict[key]['ENABLED'] = 0

    # Main loop:
    while not (controlCenter.SHUTDOWN or controlCenter.REBOOT):
        # Waits for new commands:
        controlCenter.newCmdEvent.wait()
        # Check if a refresh of the file is needed:
        if controlCenter.newCmd == 'DELETE_FILES_OBC1':
            os.system(f'rm /home/strains/OBS1/outputs/*')
        # Check if the command involves gnss-sdr:
        if "RUN_CONFIG" in controlCenter.newCmd: 
            # Extract configuration file number:
            processN = int(controlCenter.newCmd.split('_')[-1])
            # Extract the command:
            cmd = processDict[processN]['CMD']
            # Start the process if not enabled:
            if not processDict[processN]['ENABLED']:
                try:
                    # Check if other configuration files are running:
                    if any([processDict[key]['ENABLED'] for key in processDict.keys()]): killGnssSdrProcess(processDict)
                    # Run a new process:
                    print(' *** Starting a new process...\n')
                    subprocess.Popen(cmd, shell = True)
                    # Set enabled to true
                    processDict[processN]['ENABLED'] = 1
                except Exception as OSError:
                    print(' *** When calling the process something went wrong:')
                    print(f' *** {OSError}')
        # Check if a gnss-sdr process needs to be killed:
        elif any([cmd in controlCenter.newCmd for cmd in ('STOP_CONFIG', 'REBOOT_OBC', 'SHUTDOWN')]):
            # Kill gnss-sdr process
            try: killGnssSdrProcess(processDict)     
            except Exception as OSError:
                print(' *** When killing the process something went wrong:')
                print(f' *** {OSError}')
        # Clear the event:
        with controlCenter.cmdLock: controlCenter.newCmdEvent.clear()
        # Reset the status of the command:
        if not any(status in controlCenter.newCmd for status in ('REBOOT','SHUTDOWN')):
            controlCenter.switchCommand(controlCenter.newCmd, 0)
    print(" *** Stopping the thread which manage subprocess...\n")

####################################################################################################

