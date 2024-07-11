import sys, os, yaml

import numpy          as np
import xsensdeviceapi as xda

from threading import Lock
from time      import sleep
from csv       import DictWriter, writer
from utils     import csvstring, packetstring

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
        assert(packet is not 0)
        while len(self.m_packetBuffer) >= self.m_maxNumberOfPacketsInBuffer:
            self.m_packetBuffer.pop()
        self.m_packetBuffer.append(xda.XsDataPacket(packet))
        self.m_lock.release()

def runAI():

    # Open configuration file
    with open('C:\\Users\\Lorenzo\\Desktop\\retina_software\\lattepanda\\config.yaml') as d: config = yaml.full_load(d)
    with open('C:\\Users\\Lorenzo\\Desktop\\retina_software\\lattepanda\\Input\\commands.yaml') as d: commands = yaml.full_load(d)

    # Configure CSV file ------------------------------------------- #

    # Config
    header   = config['PACKETS']['AI']['FIELDNAMES']
    pathout  = config['PACKETS']['AI']['ABS_PATH']
    maxlines = config['PACKETS']['AI']['FILE_LENGTH']
    # Search for csv files
    csvfiles = [f for f in sorted(os.listdir(pathout))]
    # Count csv files
    if len(csvfiles) == 0: 
        countfile = 0
    else:
        lastfile = csvfiles[-1]
        countfile = int(lastfile.split('.')[0][-4:])
    # Create csv file
    filename   = pathout + 'AIpacket_%04i'%int(countfile) + '.csv'
    # Write header
    with open(filename, mode='a', newline='') as file:
        # Create a writer object
        writer(file).writerow(header)
        file.close()

    # Start loop
    # TODO: mettere qualche condizione, magari derivante dai telecomandi da terra   
    while not (commands.shutdown or commands.reboot):

        # Configure IMU ------------------------------------------------- #

        # Flags
        found         = False  # Flag for finding device
        opened        = False  # Flag for opening device
        created       = False  # Flag for creating control object
        stoprecording = False  # Flag for recording
        # Configuration parameters
        baud           = config['EXPERIMENT']['AI']['BAUDRATE']
        timeout        = config['EXPERIMENT']['AI']['TIMEOUT']
        packet_counter = config['EXPERIMENT']['AI']['PACKET_COUNTER']
        sample_time    = config['EXPERIMENT']['AI']['SAMPLE_TIME']
        sampling       = config['EXPERIMENT']['AI']['SAMPLING_RATE']
        exp            = 'AI'

        exceptions     = 0

        try:
            # Construct a new Xsens Device API control object
            c1 = 0
            while not created:
                print("Creating XsControl object...")
                control = xda.XsControl_construct()
                c1 +=1
                # Check if control object was created
                if control == 0:
                    sleep(5)
                elif c1 == 10:
                    raise RuntimeError("Failed creating XsControl object...")
                else:
                    created = True
                    print("XsControl object created...")
    

            print("Scanning for devices...")

            # Qui si potrebbe mettere il baud rate ESEMPIO: baudrate = XBR_9600 default 115200
            portInfoArray = xda.XsScanner_scanPorts(singleScanTimeout = timeout, ignoreNonXsensDevices = True)

            # Find an MTi device
            while not found:
                # Qui si potrebbe mettere il baud rate ESEMPIO: baudrate = XBR_9600 default 115200
                # Le cinque righe di seguito sono utili perchè scansionano tutte le porte trovate, soprattutto in caso 
                # di reset. Tuttavia per semplificare si potrebbe mettere la porta specifica
                mtPort = xda.XsPortInfo()
                for i in range(portInfoArray.size()):
                    if portInfoArray[i].deviceId().isMti():
                        mtPort = portInfoArray[i]
                        break
                    
                if mtPort.empty():
                    print()
                    raise RuntimeError("No MTi device found.")
                else:
                    did = mtPort.deviceId()
                    print("Found a device with:")
                    print(" Device ID: %s" % did.toXsString())
                    print(" Port name: %s" % mtPort.portName())

                    # Open detected port
                    print("Opening port...")
                    while not opened:
                        if not control.openPort(mtPort.portName(), mtPort.baudrate()):
                            raise RuntimeError("Could not open port...")
                        else:
                            opened = True
                            found  = True
                            # Get the device object (XsDevice)
                            device = control.device(did)
                            if device != 0:
                                print("Device: %s, with ID: %s opened." % (device.productCode(), device.deviceId().toXsString()))
                            else:
                                raise RuntimeError("Failed to connect device. Try again")

            # Create and attach callback handler to device
            callback = XdaCallback()
            device.addCallbackHandler(callback)

            # Put the device into configuration mode before configuring the device
            print("Putting device into configuration mode...")
            c2 = 0
            while True:
                if not device.gotoConfig():
                    c2 +=1
                    sleep(5)
                elif device.gotoConfig() is True:
                    break
                elif c2 == 10:
                    raise RuntimeError("Could not put device into configuration mode...")

            print("Configuring the device...")

            # Create a configuration object
            configArray = xda.XsOutputConfigurationArray()
            # Init the packet counter of the device to TODO aggiornare packet counter nel caso di reset
            configArray.push_back(xda.XsOutputConfiguration(xda.XDI_PacketCounter, 0)) #0
            # Init the sample time of the packet: VEDERE
            configArray.push_back(xda.XsOutputConfiguration(xda.XDI_SampleTimeFine, sample_time))

            # Toglierei tutto l'if e lascerei solo is AHRS
            if device.deviceId().isImu():
                # Init the acceleration acquisition frequency
                configArray.push_back(xda.XsOutputConfiguration(xda.XDI_Acceleration, sampling))
                # Init the gyro acquisition frequency
                configArray.push_back(xda.XsOutputConfiguration(xda.XDI_RateOfTurn, sampling))
                # Init the mag field acquisition frequency
                configArray.push_back(xda.XsOutputConfiguration(xda.XDI_MagneticField, sampling))
            else:
                raise RuntimeError("Unknown device while configuring. Aborting.")

            # Set the configuration
            if not device.setOutputConfiguration(configArray):
                raise RuntimeError("Could not configure the device. Aborting.")
            # Set device in measurement mode
            print("Putting device into measurement mode...")
            if not device.gotoMeasurement():
                raise RuntimeError("Could not put device into measurement mode. Aborting.")
            # Start recording
            print("Starting recording...")
            if not device.startRecording():
                raise RuntimeError("Failed to start recording. Aborting.")

            print("Main loop. Recording data")

            while not stoprecording:
                if callback.packetAvailable():
                    # Retrieve a packet
                    imu_unix = xda.XsTimeStamp_nowMs()
                    packet = callback.getNextPacket()
                    # Get packet number
                    npacket_current = packet.packetCounter()
                    npacket_all     = npacket_current + packet_counter
                    config['EXPERIMENT']['AI']['PACKET_COUNTER'] = npacket_all

                    # Get measurements
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
                            quaternion = packet.orientationQuaternion()
                        except:
                            quaternion[0] = np.nan
                            quaternion[1] = np.nan
                            quaternion[2] = np.nan  
                        try:
                            # Euler angles
                            euler = packet.orientationEuler()
                        except:
                            euler[0] = np.nan
                            euler[1] = np.nan
                            euler[2] = np.nan                    

                    input_data = [gyr[0], gyr[1], gyr[2], acc[0], acc[1], acc[2], mag[0], mag[1], mag[2], imu_unix]

                    # -------------------------------- AI ----------------------------------------------- #

                    # Do some stuff with AI
                    q0, q1, q2, q3 = 1, 0, 0, 0
                    output_data = [q0, q1 ,q2, q3]

                    # -------------------------------- WRITE CSV ---------------------------------------- #
                    try:
                        if (npacket_all%maxlines) == 0:
                            # Create a new file
                            countfile += 1
                            filename   = pathout + 'AIpacket_%04i'%int(countfile) + '.csv'
                            # Create header
                            with open(filename, mode='a', newline='') as file:
                                # Create a writer object
                                writer(file).writerow(header)
                                file.close()
                        # write csv
                        data_csv = csvstring(input_data, output_data, npacket_all, exp)
                        with open(filename, mode='a', newline='') as file:
                            # Create a writer object
                            DictWriter(file, fieldnames=header).writerows(data_csv)
                            file.close()
                        if (npacket_all%10) == 0:
                            # send to udoo
                            try:
                                data_udoo = packetstring(input_data, output_data, npacket_all, exp)
                                a = 1
                            except:
                                print('Failed to send packet to udoo')
                        
                    except:
                        raise RuntimeError("Failed writing csv")
                    
                    if (commands.shutdown or commands.reboot):
                        stoprecording = True
                    # ----------------------------------------------------------------------------------- #
            print("\nStopping recording...")
            if not device.stopRecording():
                raise RuntimeError("Failed to stop recording...")

            print("Closing log file...")
            if not device.closeLogFile():
                raise RuntimeError("Failed to close log file....")

            print("Removing callback handler...")
            device.removeCallbackHandler(callback)
            # Close port
            print("Closing port...")
            control.closePort(mtPort.portName())
            # Close XsControl object
            print("Closing XsControl object...")
            control.close()

        except RuntimeError as error:
            print(error)
            found         = False
            opened        = False
            created       = False
            stoprecording = True
            exceptions    += 1

            if exceptions == 10:
                sys.exit(1)
                #reset

        except:
            print("An unknown fatal error has occured. Aborting.")
            found         = False
            opened        = False
            created       = False
            stoprecording = True
            exceptions    += 1 

            if exceptions == 10:
                sys.exit(1)
                #reset
        else:
            print("Successful exit.")

def runGNSS():

    with open('C:\\Users\\Lorenzo\\Desktop\\retina_software\\lattepanda\\Input\\config.yaml') as d: config = yaml.full_load(d)
    with open('C:\\Users\\Lorenzo\\Desktop\\retina_software\\lattepanda\\Input\\commands.yaml') as d: commands = yaml.full_load(d)

    packet_counter = config['EXPERIMENT']['GNSS']['PACKET_COUNTER']
    exceptions = 0
    exp = 'GNSS'

    # Configure CSV file ------------------------------------------- #

    # Config
    header   = config['PACKETS']['GNSS']['FIELDNAMES']
    pathout  = config['PACKETS']['GNSS']['ABS_PATH']
    maxlines = config['PACKETS']['GNSS']['FILE_LENGTH']
    # Search for csv files
    csvfiles = [f for f in sorted(os.listdir(pathout))]
    # Count csv files
    if len(csvfiles) == 0: 
        countfile = 0
    else:
        lastfile = csvfiles[-1]
        countfile = int(lastfile.split('.')[0][-4:])
    # Create csv file
    filename = pathout + 'GNSSpacket_%04i'%int(countfile) + '.csv'
    # Write header
    with open(filename, mode='a', newline='') as file:
        # Create a writer object
        writer(file).writerow(header)
        file.close()
        
        # Configure GNSS ------------------------------------------------- #

        # Use GNSS

        while not (commands.shutdown or commands.reboot):
            sleep(1)
            # Write CSV
            try:
                stoprecording = False
                while not stoprecording:
                    config['EXPERIMENT']['GNSS']['PACKET_COUNTER'] = packet_counter

                    carrier1 = 0
                    pseudo1  = 0
                    doppler1 = 0
                    carrier2 = 0
                    pseudo2  = 0
                    doppler2 = 0
                    lat = 0
                    lon = 0
                    alt = 0
                    input_data = [carrier1, pseudo1, doppler1, carrier2, pseudo2, doppler2]
                    output_data = [lat,lon,alt]
                    try:
                        if (packet_counter%maxlines) == 0:
                            # Create a new file
                            countfile += 1
                            filename   = pathout + 'GNSSpacket_%04i'%int(countfile) + '.csv'
                            # Create header
                            with open(filename, mode='a', newline='') as file:
                                # Create a writer object
                                writer(file).writerow(header)
                                file.close()
                        # write csv
                        data = csvstring(input_data, output_data, packet_counter, exp)
                        with open(filename, mode='a', newline='') as file:
                            # Create a writer object
                            DictWriter(file, fieldnames=header).writerows(data)
                            file.close()
                    except:
                        raise RuntimeError("Failed writing csv")
                    packet_counter += 1
                    
            except RuntimeError as error:
                a=1
                print(error)
                
            except: 

                print("An unknown fatal error has occured. Aborting.")

                exceptions    += 1 

                if exceptions == 10:
                    sys.exit(1)
                    #reset


if __name__ == '__main__':
    runAI()
