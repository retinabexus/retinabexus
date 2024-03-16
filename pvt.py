# Copyright (C) 2015-2021 Swift Navigation Inc.
# Contact: https://support.swiftnav.com
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.
"""
the :mod:`sbp.client.examples.simple` module contains a basic example of
reading SBP messages from a serial port, decoding BASELINE_NED messages and
printing them out.
"""

from sbp.client.drivers.pyserial_driver import PySerialDriver
from sbp.client import Handler, Framer
from sbp.navigation import SBP_MSG_GPS_TIME
from sbp.navigation import SBP_MSG_POS_ECEF
from sbp.imu import SBP_MSG_IMU_RAW
from sbp.piksi import SBP_MSG_DEVICE_MONITOR
from sbp.navigation import SBP_MSG_POS_LLH
from sbp.navigation import SBP_MSG_VEL_ECEF

from sbp.mag import SBP_MSG_MAG_RAW

import os
from datetime import datetime, timedelta
from dataclasses import dataclass
from time import sleep

#################################################################################################

@dataclass
class PiksiPacket:
    """
    Dataclass for the piksi packet.
    """  
    experiment: str = ''
    type: str = ''
    number: int = 0
    date: str = ''
    lat: float = 0.
    lon: float = 0.
    height: float = 0.
    posx: float = 0.
    posy: float = 0.
    posz: float = 0.
    velx: float = 0.
    vely: float = 0.
    velz: float = 0.
    nsats: int = 0
    gyrx: float = 0.
    gyry: float = 0.
    gyrz: float = 0.
    magx: float = 0.
    magy: float = 0.
    magz: float = 0.
    cputemp: str = 'None'

    def __repr__(self) -> str:
        return self.experiment + "," + self.type + "," + f"{self.number}" + ","\
                + f"{self.date}" + "," + f'{self.lat}' + "," + f'{self.lon}' + ","\
                + f'{self.height}' + "," + f'{self.posx}' + "," + f'{self.posy}' + ","\
                + f'{self.posz}' + "," + f'{self.velx}' + "," + f'{self.vely}' + ","\
                + f'{self.velz}' + "," + f'{self.nsats}' + "," + f'{self.gyrx}' + ","\
                + f'{self.gyry}' + "," + f'{self.gyrz}' + "," + f'{self.magx}' + ","\
                + f'{self.magy}' + "," + f'{self.magz}' + "," + f'{self.cputemp}' 

#################################################################################################

class Piksi:

    def __init__(self, config: dict):
        """
        __init__ method for the Piksi class.
        
            Args: 
            - Configuration dictionary 
        """     

        # Configurarion:    
        serialPort   = config['PIKSI']['SERIAL_PORT']
        baudRate     = config['PIKSI']['BAUD_RATE']
        configList   = config['PIKSI']['CONFIG_LIST']
        visualizer   = config['PIKSI']['VISUALIZER']
        self.cpuFreq = int(config['PIKSI']['CPU_FREQ'])

        # Initialization:
        self.serialPort = serialPort
        self.baudRate = baudRate
        #self.changeSettings(configList, visualizer) 
        self.gpsEpoch = datetime(1980,1,6)
        
    
    def changeSettings(self, configList: list, visualizer: bool):
        """
        Method to change piksi settings.

            Args: 
            - List of settings
            - Boolean variable to visualize the settings
        """
        # The list of settings is composed by strings. Each string has 3 elements, separated by a space. 
        # The first one is the macro area of the settings pannel in swift console (ex:acquisition, ethernet, ...)
        # The second one is the area inside the macroarea(ex:glonass acquisition, sbas acquisition, ...)
        # The third one is the value that one wants to set (ex.True, False, ...)
        # If the visualizer is True, one can see from the terminal all the settings of the swift console
        settingsEnabled = False
        while not settingsEnabled:
            try:
                for config in configList:
                    os.system("python -m piksi_tools.settings  -p " + self.serialPort + " write " + config)
                if visualizer:
                    os.system("python -m piksi_tools.settings  -p " + self.serialPort + " all") #read all the defoult settings of the piksi multi
            except Exception as error:
                print(f" *** While enabling piksi settings something went wrong:")
                print(f" *** {error}")
                print(f" *** Trying again...\n")
                sleep(5)
            else:
                settingsEnabled = True
                print("\n *** Connected to Piksi port: " + self.serialPort + "...\n")

        
    def buildPacket(self, piksiPacket: PiksiPacket):
        """
        Method to read piksi data.

            Args: 
            - Object of the dataclass PiksiPacket

            Returns:
            - Built PiksiPacket
        """
        try:
            
            # Get Piksi data:
            with PySerialDriver(self.serialPort, baud=self.baudRate) as driver:
                with Handler(Framer(driver.read, None, verbose=True)) as source: 
    
                    # Nominal solution
                    sourceFilterTime    = (source.filter(SBP_MSG_GPS_TIME).__next__())[0] 
                    sourceFilterLLH     = (source.filter(SBP_MSG_POS_LLH).__next__())[0]  
                    sourceFilterPosECEF = (source.filter(SBP_MSG_POS_ECEF).__next__())[0]  
                    sourceFilterVelECEF = (source.filter(SBP_MSG_VEL_ECEF).__next__())[0]  
                    sourceFilterImu     = (source.filter(SBP_MSG_IMU_RAW).__next__())[0]
                    sourceFilterMag     = (source.filter(SBP_MSG_MAG_RAW).__next__())[0]       
                    wn                  = sourceFilterTime.wn
                    tow                 = sourceFilterTime.tow
                    nanos               = sourceFilterTime.ns_residual               
                    piksiPacket.lat     = sourceFilterLLH.lat
                    piksiPacket.lon     = sourceFilterLLH.lon
                    piksiPacket.height  = sourceFilterLLH.height                 
                    piksiPacket.posx    = sourceFilterPosECEF.x
                    piksiPacket.posy    = sourceFilterPosECEF.y
                    piksiPacket.posz    = sourceFilterPosECEF.z
                    piksiPacket.velx    = sourceFilterVelECEF.x
                    piksiPacket.vely    = sourceFilterVelECEF.y
                    piksiPacket.velz    = sourceFilterVelECEF.z
                    piksiPacket.nsats   = sourceFilterPosECEF.n_sats                    
                    piksiPacket.gyrx    = sourceFilterImu.gyr_x
                    piksiPacket.gyry    = sourceFilterImu.gyr_y
                    piksiPacket.gyrz    = sourceFilterImu.gyr_z
                    piksiPacket.magx    = sourceFilterMag.mag_x
                    piksiPacket.magy    = sourceFilterMag.mag_y
                    piksiPacket.magz    = sourceFilterMag.mag_z
                    utcDate             = self.gpsEpoch + timedelta(weeks=wn,milliseconds=tow+nanos/1000,seconds=-18)
                    piksiPacket.date    = utcDate
                    
                    # Add cpu temperature
                    if piksiPacket.number%self.cpuFreq == 0:
                        piksiPacket.cputemp = (source.filter(SBP_MSG_DEVICE_MONITOR).__next__())[0].cpu_temperature*1e-2
                    else: piksiPacket.cputemp = 'None'   
                    
        except Exception as error:
            print(f"\n *** While reading piksi data something went wrong:") 
            print(f" *** {error}\n")            
        finally: return piksiPacket
          
#################################################################################################