import sys, os, yaml

import functions      as fn
import numpy          as np
import xsensdeviceapi as xda
import serial
import torch
import pickle

from sklearn.preprocessing import StandardScaler
from datetime  import datetime, timezone
from threading import Lock
from time      import sleep, time
from csv       import DictWriter, writer
from utils     import csvstring, packetstring, log_message, write_log
from utils_AI  import*
from telecommands import send_data


class XdaCallback(xda.XsCallback):
    def __init__(self, max_buffer_size = 5):
        xda.XsCallback.__init__(self)
        self.m_maxNumberOfPacketsInBuffer = max_buffer_size
        self.m_packetBuffer = list()
        self.m_lock = Lock()

    def packetAvailable(self):
        self.m_lock.acquire()
        res = len(self.m_packetBuffer) > 0
        self.m_lock.release()
        return res

    def getNextPacket(self):
        self.m_lock.acquire()
        assert(len(self.m_packetBuffer) > 0)
        oldest_packet = xda.XsDataPacket(self.m_packetBuffer.pop(0))
        self.m_lock.release()
        return oldest_packet

    def onLiveDataAvailable(self, dev, packet):
        self.m_lock.acquire()
        assert(packet != 0)
        while len(self.m_packetBuffer) >= self.m_maxNumberOfPacketsInBuffer:
            self.m_packetBuffer.pop()
        self.m_packetBuffer.append(xda.XsDataPacket(packet))
        self.m_lock.release()

def getIMU(packet):
    
    # Init lists
    acc, gyr, mag, quat = [], [], [], []
    if packet.containsCalibratedData():
        # Acceleration
        try:
            acc = packet.calibratedAcceleration()
        except:
            acc[0] = np.nan
            acc[1] = np.nan
            acc[2] = np.nan
        # Gyroscope
        try:
            gyr = packet.calibratedGyroscopeData()
        except:
            gyr[0] = np.nan
            gyr[1] = np.nan
            gyr[2] = np.nan
        # Magnetic field
        try:
            mag = packet.calibratedMagneticField()
        except:
            mag[0] = np.nan
            mag[1] = np.nan
            mag[2] = np.nan
    # Get orientation
    if packet.containsOrientation():
        # Quaternions
        try:
            quat   = packet.orientationQuaternion()
        except:
            quat[0] = np.nan
            quat[1] = np.nan
            quat[2] = np.nan  
            quat[3] = np.nan
    # Get time TODO: epoca iniziale
    if packet.containsUtcTime():
        imu_unix = packet.utcTime()  
        epoch    = time()
        utc_dt   = datetime(imu_unix.m_year, imu_unix.m_month, imu_unix.m_day, imu_unix.m_hour, imu_unix.m_minute, imu_unix.m_second,int(imu_unix.m_nano/1000), tzinfo=timezone.utc)
        unix_dt  = utc_dt.timestamp()
        imu_unix = epoch + unix_dt


    input_data = [gyr[0], gyr[1], gyr[2], acc[0], acc[1], acc[2], mag[0], mag[1], mag[2], imu_unix, quat[0], quat[1], quat[2], quat[3]]
    return input_data

def runAI(config, commands):

    # Configure output files ------------------------------------------------------------- #

    # Config
    header   = config['PACKETS']['AI']['FIELDNAMES']
    pathcsv  = config['PACKETS']['AI']['ABS_PATH']
    maxlines = config['PACKETS']['AI']['FILE_LENGTH']
    pathfb   = config['PACKETS']['FEEDBACKS']['FILE_PATH']

    # Search for csv files
    csvfiles = [f for f in sorted(os.listdir(pathcsv))]
    # Count csv files
    if len(csvfiles) == 0: 
        countfile = 1
    else:
        lastfile = csvfiles[-1]
        countfile = int(lastfile.split('.')[0][-4:])+1

    # Create csv file
    filename   = pathcsv + 'AIpacket_%04i'%int(countfile) + '.csv'
    
    # Write header
    with open(filename, mode='a', newline='') as file:
        # Create a writer object
        writer(file).writerow(header)

    # Start loop ------------------------------------------------------------------------- #
    exceptions = 0

    # TODO: mettere qualche condizione, magari derivante dai telecomandi da terra   
    while True:

        # Configure link ----------------------------------------------- #
        port_link    = config['PACKETS']['LINK']['PORT']
        baud_link    = config['PACKETS']['LINK']['BAUDRATE']
        timeout_link = config['PACKETS']['LINK']['TIMEOUT']

        ser = serial.Serial(port_link, baud_link, timeout_link)
                         
        # Configure AI ------------------------------------------------- #
        seq_len        = config['EXPERIMENT']['AI']['SEQUENCE_LENGTH']
        model          = config['EXPERIMENT']['AI']['MODEL_PATH']
        scaler         = config['EXPERIMENT']['AI']['SCALER_PATH']

        # carica i parametri per normalizzare i dati in input per la coerenza con l'allenamento 
        with open(scaler, 'rb') as f:
            loaded_scaler = pickle.load(f)

        # carica i parametri per la rete dati dall'allenamento
        loaded_model = torch.load(model, map_location=torch.device('cpu'))

        # Configure IMU ------------------------------------------------- #

        # Flags
        found         = False  # Flag for finding device
        opened        = False  # Flag for opening device
        created       = False  # Flag for creating control object
        stoprecording = False  # Flag for recording

        # Configuration parameters
        baud           = config['EXPERIMENT']['AI']['BAUDRATE']
        port           = config['EXPERIMENT']['AI']['PORT']
        packet_counter = config['EXPERIMENT']['AI']['PACKET_COUNTER']
        sample_time    = config['EXPERIMENT']['AI']['SAMPLE_TIME']
        sampling       = config['EXPERIMENT']['AI']['SAMPLING_RATE']
        wdt            = config['EXPERIMENT']['AI']['WDT']
        exp            = 'AI'
        if baud == 115200: xbrbaud = xda.XBR_115k2

        try:
            # Construct a new Xsens Device API control object
            c1 = 0
            while not created:
                message = "Creating XsControl object..."
                print(message)
                write_log(log_message(message), pathfb)
                control = xda.XsControl_construct()
                c1 +=1
                # Check if control object was created
                if control == 0:
                    sleep(5)
                elif c1 == 10:
                    raise RuntimeError("Failed creating XsControl object...")
                else:
                    created = True
                    message = "XsControl object created..."
                    print(message)
                    write_log(log_message(message), pathfb)

            message = "Scanning for devices..."
            print(message)
            write_log(log_message(message), pathfb)

            # Scan serial ports
            portInfoArray =  xda.XsScanner_scanPort(xda.XsString(port), xbrbaud)
            # Find an MTi device
            while not found:
                mtPort = xda.XsPortInfo()
                if portInfoArray.deviceId().isAhrs():
                    mtPort = portInfoArray

                if mtPort.empty():
                    print()
                    raise RuntimeError("No MTi device found.")
                else:
                    did = mtPort.deviceId()
                    message = f"Found a device with Device ID: {did.toXsString()} at Port: {mtPort.portName()}"
                    print(message)
                    write_log(log_message(message), pathfb)

                    # Open detected port
                    message = "Opening port..."
                    print(message)
                    write_log(log_message(message), pathfb)
                    while not opened:
                        if not control.openPort(mtPort.portName(), mtPort.baudrate()):
                            raise RuntimeError("Could not open port...")
                        else:
                            opened = True
                            found  = True
                            # Get the device object (XsDevice)
                            device = control.device(did)
                            if device != 0:
                                message = "Device: %s, with ID: %s opened." % (device.productCode(), device.deviceId().toXsString())
                                print(message)
                                write_log(log_message(message), pathfb)
                            else:
                                raise RuntimeError("Failed to connect device. Try again")

            # Create and attach callback handler to device
            callback = XdaCallback()
            device.addCallbackHandler(callback)

            # Put the device into configuration mode before configuring the device
            message = "Putting device into configuration mode..."
            print(message)
            write_log(log_message(message), pathfb)
            c2 = 0
            while True:
                if not device.gotoConfig():
                    c2 +=1
                    sleep(5)
                elif device.gotoConfig() is True:
                    break
                elif c2 == 10:
                    raise RuntimeError("Could not put device into configuration mode...")

            message = "Configuring the device..."
            print(message)
            write_log(log_message(message), pathfb)
            # Create a configuration object
            configArray = xda.XsOutputConfigurationArray()
            # Init the packet counter of the device to TODO aggiornare packet counter nel caso di reset
            configArray.push_back(xda.XsOutputConfiguration(xda.XDI_PacketCounter, 0)) #0
            # Init the sample time of the packet: VEDERE
            configArray.push_back(xda.XsOutputConfiguration(xda.XDI_SampleTimeFine, sample_time))

            if device.deviceId().isAhrs():
                # Init the acceleration acquisition frequency
                configArray.push_back(xda.XsOutputConfiguration(xda.XDI_Acceleration, sampling))
                # Init the gyro acquisition frequency
                configArray.push_back(xda.XsOutputConfiguration(xda.XDI_RateOfTurn, sampling))
                # Init the mag field acquisition frequency
                configArray.push_back(xda.XsOutputConfiguration(xda.XDI_MagneticField, sampling))
                # Init the quaternion acquisition frequency
                configArray.push_back(xda.XsOutputConfiguration(xda.XDI_Quaternion, sampling))
                # Init the quaternion acquisition frequency
                configArray.push_back(xda.XsOutputConfiguration(xda.XDI_UtcTime, sampling))
            else:
                raise RuntimeError("Unknown device while configuring. Aborting.")

            # Set the configuration
            if not device.setOutputConfiguration(configArray):
                raise RuntimeError("Could not configure the device. Aborting.")
            # Set device in measurement mode
            message = "Putting device into measurement mode..."
            print(message)
            write_log(log_message(message), pathfb)
            if not device.gotoMeasurement():
                raise RuntimeError("Could not put device into measurement mode. Aborting.")
            # Start recording
            message = "Starting recording..."
            print(message)
            write_log(log_message(message), pathfb)
            if not device.startRecording():
                raise RuntimeError("Failed to start recording. Aborting.")

            count = 0
            buffer_seq = []
            # Recording loop
            while not stoprecording:
                if callback.packetAvailable():
                    # Retrieve a packet
                    #imu_unix = xda.XsTimeStamp_nowMs()
                    packet = callback.getNextPacket()
                    # Get packet number
                    npacket_current = packet.packetCounter()
                    npacket_all     = npacket_current + packet_counter
                    # Get measurements TODO: IRROBUSTIRE
                    input_data = getIMU(packet)
                    # TODO: controllo su dati presenti e mettere nan altrimenti

                    # Init sequence
                    if count < seq_len:
                        buffer_seq.append(input_data)
                        count +=1
                    else:
                        buffer_seq.pop(0)
                        buffer_seq.append(input_data)
                    # -------------------------------- AI ----------------------------------------------- #
                    if len(buffer_seq) == seq_len:
                        inputAI = [row[:6] for row in buffer_seq]
                        
                        y = AI(inputAI,loaded_model,loaded_scaler)
                        q0, q1, q2, q3 = y[0,0], y[0,1], y[0,2], y[0,3]
                        output_data = [q0, q1 ,q2, q3]
                    else:
                        output_data = [0, 0, 0, 0]

                    # -------------------------------- WRITE CSV ---------------------------------------- #
                    try:
                        if (npacket_all%maxlines) == 0:
                            # Create a new file
                            countfile += 1
                            filename   = pathcsv + 'AIpacket_%04i'%int(countfile) + '.csv'
                            # Create header
                            with open(filename, mode='a', newline='') as file:
                                # Create a writer object
                                writer(file).writerow(header)
                        # write csv
                        data_csv = csvstring(input_data, output_data, npacket_all, exp)
                        with open(filename, mode='a', newline='') as file:
                            DictWriter(file, fieldnames=header).writerows(data_csv)
                        if (npacket_all%10) == 0:
                            # send to udoo
                            try:
                                data_udoo = packetstring(input_data, output_data, npacket_all, exp)
                                send_data(data_udoo,ser)
                            except:
                                message = 'Failed sending data to OBC1'
                                print(message)
                                write_log(log_message(message), pathfb)                        
                    except:
                        raise RuntimeError("Failed writing csv")
                else:
                    # Watchdog timer in case of absence of packets
                    starttimer = time()
                    while True:
                        if callback.packetAvailable():
                            break
                        elif time() - starttimer > wdt:
                            raise RuntimeError("Connection lost")
                                      
            message = "Stop recording..."
            print(message)
            write_log(log_message(message), pathfb)
            if not device.stopRecording():
                raise RuntimeError("Failed to stop recording...")

            print("Closing log file...")
            if not device.closeLogFile():
                raise RuntimeError("Failed to close log file....")

            print("Removing callback handler...")
            device.removeCallbackHandler(callback)
            # Close port
            message = "Closing port..."
            print(message)
            write_log(log_message(message), pathfb)
            control.closePort(mtPort.portName())
            # Close XsControl object
            message = "Closing XsControl object..."
            print(message)
            write_log(log_message(message), pathfb)
            control.close()

        except RuntimeError as error:
            print(error)
            write_log(log_message(error), pathfb)
            # Close port
            if control != 0:
                control.closePort(mtPort.portName())
                control.close()
            sleep(10)
            exceptions += 1

            if exceptions == 10:
                # Send info to ground
                sleep(60*5)
                # Reboot
                message = "Automatic reboot in progress"
                print(message)
                write_log(log_message(message), pathfb)
                reboot = commands['COMMANDS']['INNER']['REBOOT']
                exec_cmd(reboot)

        except:
            message  = "An unknown fatal error has occured"
            print(message)
            write_log(log_message(message), pathfb)
            # Close port
            if control != 0:
                control.closePort(mtPort.portName())
                control.close()
            sleep(10)
            exceptions += 1 

            # Watchdog to reboot after 10 exceptions TODO: fun
            if exceptions == 10:
                # Send info to ground
                sleep(60*5)
                # Reboot
                message = "Automatic reboot in progress"
                print(message)
                write_log(log_message(message), pathfb)
                reboot = commands['COMMANDS']['INNER']['REBOOT']
                exec_cmd(reboot)
        else:
            print("Successful exit.")

def runGNSS(config):

    packet_counter = config['EXPERIMENT']['GNSS']['PACKET_COUNTER']
    exceptions = 0
    exp = 'GNSS'

    # Configure output files ----------------------------------------- #

    # Config
    pathout  = config['PACKETS']['GNSS']['ABS_PATH']
    maxlines = config['PACKETS']['GNSS']['FILE_LENGTH']
    pathfb   = config['PACKETS']['FEEDBACKS']['FILE_PATH']

    # Search for csv files
    csvfiles = [f for f in sorted(os.listdir(pathout))]
    # Count csv files
    if len(csvfiles) == 0: 
        countfile = 1
    else:
        lastfile = csvfiles[-1]
        countfile = int(lastfile.split('.')[0][-4:]) + 1
    # Create csv file
    filename = pathout + 'GNSSpacket_%04i'%int(countfile) + '.csv'
    # Write header
    #with open(filename, mode='a', newline='') as file:
    #    # Create a writer object
    #    writer(file).writerow(header)
    #    file.close()
    
    while True:

        try:

            # Configure GNSS ------------------------------------------------- #

            message = "Starting GNSS cofiguration..."
            print(message)
            write_log(log_message(message), pathfb)

            port     = config['EXPERIMENT']['GNSS']['PORT']
            baudrate = config['EXPERIMENT']['GNSS']['BAUDRATE']
            timeout  = config['EXPERIMENT']['GNSS']['TIMEOUT']

            sleep(10)

            # Open serial
            serGNSS = serial.Serial(port, baudrate, timeout)

            if serGNSS.isOpen():
                tosend = ['obsvma 1', 'obsvha 1', 'bestnava 2', 'bestnavha 2', 'galepha 1', 'gloepha 1', 'gpsepha 1', 'bdsepha 1']
                for c in tosend:
                    serGNSS.write(c.encode('utf-8') + b'\r\n')
            
                # TODO: read response and check config
                if True:
                    message = "Configuration completed"
                    print(message)
                    write_log(log_message(message), pathfb)
                else:
                    raise RuntimeError("Configuration failed")
            else: 
                raise RuntimeError("Port is not opened")

            # Use GNSS ------------------------------------------------------- #
            print("Start acquisition\n")
            while True:
                
                try:
                    # Read serial port ------------------------------------------------------------- #
                    line = serGNSS.readline().strip()
                except:
                    raise RuntimeError("Error reading serial port")

                if line:

                    # Write CSV ---------------------------------------------------------------- #
                    try:
                        if (packet_counter%maxlines) == 0:
                            # Create a new file
                            countfile += 1
                            filename   = pathout + 'GNSSpacket_%04i'%int(countfile) + '.csv'

                        # write csv
                        with open(filename, mode='a') as file:
                            # Create a writer object
                            writer(file).writerow([line.decode("utf-8").replace('\00',"")])
                    except:
                        raise RuntimeError("Failed writing csv")  
                                          
        except RuntimeError as error:
            print(error)
            write_log(log_message(message), pathfb)
            if serGNSS.isOpen():
                # Close port
                print("Closing port...")
                serGNSS.close()
            sleep(10)
            exceptions += 1 
            # Watchdog to reboot after 10 exceptions TODO: fun
            #if exceptions == 10:
            #    # Send info to ground
            #    sleep(60*5)
            #    # Reboot
            #    message = "Automatic reboot in progress"
            #    print(message)
            #    write_log(log_message(message), pathfb)
            #    reboot = commands['COMMANDS']['INNER']['REBOOT']
            #    cmd = 'sudo %s'% reboot
            #    os.system(cmd)
           
        except: 
            message  = "An unknown fatal error has occured"
            print(message)
            write_log(log_message(message), pathfb)
            if serGNSS.isOpen():
                # Close port
                print("Closing port...")
                serGNSS.close()
            sleep(10)
            exceptions += 1 
            # Watchdog to reboot after 10 exceptions TODO: fun
            #if exceptions == 10:
            #    # Send info to ground
            #    sleep(60*5)
            #    # Reboot
            #    message = "Automatic reboot in progress"
            #    print(message)
            #    write_log(log_message(message), pathfb)
            #    reboot = commands['COMMANDS']['INNER']['REBOOT']
            #    cmd = 'sudo %s'% reboot
            #    os.system(cmd)

def test_uart():


    # Set up the serial connection (adjust 'COM3' to your port and baud rate as needed)
    ser = serial.Serial(
        port='/dev/ttyUSB0',  # Replace with your port name
        baudrate=9600,  # Baud rate
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=1
    )

    try:
        # Example usage
        send_data("Hello UART",ser)
        sleep(1)  # Wait for a moment to ensure data is received
        receive_data(ser)

    except Exception as e:
        print(f"Error: {e}")

    finally:
        ser.close()  # Close the serial connection
if __name__ == '__main__':
    runAI()
