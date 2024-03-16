import serial, select
from datetime import datetime
from threading import Lock

from ina219 import INA219
from csv import DictWriter

from dataclasses import dataclass
from time import sleep


#################################################################################################

@dataclass
class TelemetryPacket:
    """
    Dataclass for the telemetry packet.
    """  
    experiment: str = ''
    type: str = ''
    number: int = 0
    date: datetime = ''
    cpu_temp: str = ''
    sens_press: str = ''
    sens_temp: str = ''
    temp0: str = ''
    temp1: str = ''
    temp2: str = ''
    temp3: str = ''
    temp4: str = ''
    volt: str = ''
    curr: str = ''
    pow: str = ''

    def __repr__(self) -> str:
        return self.experiment + "," + self.type + "," + f"{self.number}" + ","\
            + f"{self.date}" + "," + f"{self.cpu_temp}" + "," + f"{self.sens_press}" + "," + f"{self.sens_temp}" + ","\
            + f"{self.temp0}" + "," + f"{self.temp1}" + "," + f"{self.temp2}" + "," + f"{self.temp3}" + "," + f"{self.temp4}" + ","\
            + f"{self.volt}" + "," + f"{self.curr}" + "," + f"{self.pow}"

#################################################################################################

class Nano:

    def __init__(self, config: dict):
        """
        __init__ method for the Arduino class.
        An Arduino object handles Arduino serial communication and packets.

            Args: 
            - Configuration dictionary 
        """

        # Configurarion:    
        serialPort = config['NANO']['SERIAL_PORT']
        baudRate = config['NANO']['BAUD_RATE']

        # Initialization:
        self.config = config                    
        self.connect(serialPort, baudRate)  
        self.nanoLock = Lock()

    def connect(self, serialPort: str, baudRate: int):
        """
        Method to create the serial object.

            Args: 
            - Serial port for Arduino communication
            - Baud rate for the Arduino communication
        """
        try:
            # Create the serial object:
            self.serialObj = serial.Serial(serialPort, baudRate)          
            print("\n *** Connected to Arduino port: " + serialPort + "...\n")
        except Exception as error:
            print(" *** Unable to connect to Arduino:")
            print(f" *** {error}")
            print(" *** Please try again...\n")
            sleep(5)
            # Try again to connect:
            self.connect(serialPort, baudRate)  

    def extractData(self, dataList: list, ready: bool):
        """
        Method to extract Arduino sensors data from the serial monitor reading.

            Args: 
            - Serial monitor reading splitted [start, press, temp, end]
            - Select output

            Returns:
            - Sensors data [press, temp]
        """  
        # Check if ready:
        if ready:
            # Check lecture:
            if (isinstance(dataList, list)) and (dataList[0] == 'start') and (dataList[-1] == 'end'):
                return dataList[1:-1]
            # Invalid reading:
            print(" *** Invalid Arduino reading\n")
            return ["None"]*self.config['PACKETS']['TELEMETRY']['DATA_LENGTH']
        # None reading:
        print(" *** Arduino didn't read anything\n")
        return ["None"]*self.config['PACKETS']['TELEMETRY']['DATA_LENGTH']

    def buildPacket(self, telemetryPacket: TelemetryPacket):
        """
        Method to read Arduino data (with timeout).

            Args: 
            - Object of the dataclass TelemetryPacket

            Returns:
            - Telemetry packet (updated)
        """
        
        # Listen for new inputs: 
        timeout = self.config['PACKETS']['TELEMETRY']['TIMEOUT']
        ready, _, _ = select.select([self.serialObj], [], [], timeout)
        try:
            # Read line from the serial monitor:
            with self.nanoLock: data = self.serialObj.readline()  
            data = data.decode('utf-8').rstrip("\r\n") 
            # Convert to a list:
            dataList = data.split(",")
            # Extract data:
            dataList = self.extractData(dataList, ready)
            # Add to the packet:
            telemetryPacket.sens_press = dataList[0]
            telemetryPacket.sens_temp  = dataList[1]
            telemetryPacket.temp0      = dataList[2]
            telemetryPacket.temp1      = dataList[3]
            telemetryPacket.temp2      = dataList[4]
            telemetryPacket.temp3      = dataList[5]
            telemetryPacket.temp4      = dataList[6]
        except Exception as error:
            print(f" *** While reading serial monitor something went wrong:") 
            print(f" *** {error}\n")  
        finally: return telemetryPacket

    def serialWrite(self, cmd: str):
        """
        Method to write to Arduino from Raspberry.

            Args: 
            - Command to send
        """
        # Send command to arduino:
        try:
            with self.nanoLock: self.serialObj.write(cmd.encode('utf-8'))
        except Exception as error:
            print(f" *** While writing to serial monitor something went wrong:") 
            print(f" *** {error}\n")  

    def close(self):
        """
        Method to close the serial communication.
        """
        try:
            # Close the serial communication:
            print(" *** Closing connection with Arduino...\n")
            with self.nanoLock: self.serialObj.close()    
        except Exception as error:
            print(f" *** While closing serial communication something went wrong:") 
            print(f" *** {error}\n")

#################################################################################################

class Raspy:

    def __init__(self, config: dict):
        """
        __init__ method for the Raspy class.
        A Raspy object reads data from the INA219 sensors.

            Args: 
            - Configuration dictionary
        """ 

        # Configuration:
        SHUNT_OHMS = config['INA']['SHUNT_OHMS']
        MAX_EXPECTED_AMPS = config['INA']['MAX_EXPECTED_AMPS']
        INA_ADDRESS = config['INA']['ADDRESS']
        BUSNUM = config['INA']['BUSNUM']

        # Initialization:
        try:
            self.ina = INA219(shunt_ohms = SHUNT_OHMS, max_expected_amps = MAX_EXPECTED_AMPS, address = INA_ADDRESS, busnum = BUSNUM)
            self.ina.configure(self.ina.RANGE_16V)  # 16 V OR 32 V (for INA219 only 16)
        except Exception as error:
            print(" *** Unable to configure INA219:")
            print(f" *** {error}\n") 
        

    def buildPacket(self, telemetryPacket: TelemetryPacket):
        """
        Method to read INA219 data (with timeout).

            Args: 
            - Object of the dataclass TelemetryPacket

            Returns:
            - Sensors data [voltage, current, power]
        """
        # Listen for new inputs:
        try:
            # Add to the packet INA219 data:
            telemetryPacket.volt = "%.3f"%(self.ina.voltage())  # V
            telemetryPacket.curr = "%.3f"%(self.ina.current())  # mA
            telemetryPacket.pow  = "%.3f"%(self.ina.power())    # mW
        except Exception as error:
            print(f" *** While reading INA219 something went wrong:") 
            print(f" *** {error}\n")
        finally: return telemetryPacket

#################################################################################################
