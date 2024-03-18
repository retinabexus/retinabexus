from threading import Lock, Event
from datetime import datetime
from dataclasses import dataclass

###################################################################################

@dataclass
class FeedbackPacket:

    experiment: str = ''
    type: str = ''
    number: int = 0
    date: datetime = None
    fdb: int = None

    def __repr__(self) -> str:
        return self.experiment + "," + self.type + "," + f"{self.number}" + ","\
            + f"{self.date}" + "," + f"{self.fdb}" 

####################################################################################

def isCommandPacket(packet: list, config: dict):
    """
    Function to verify the received TCP packet.

        Args: 
        - Received TCP packet (splitted)
        - Configuration dictionary

        Returns:
        - True/False
    """  
    return (isinstance(packet, list)) \
        and (len(packet) == config['PACKETS']['COMMANDS']['DATA_LENGTH']) \
        and (packet[0] == config['PACKETS']['COMMANDS']['EXPERIMENT_ID'])\
        and (packet[1] == config['PACKETS']['COMMANDS']['PACKET_ID'])

###################################################################################

class ControlCenter:

    def __init__(self, obcNumber: int, cmdDict: dict):
        """
        __init__ method for the ControlCenter class.

            Args: 
            - OBC number (1/2)
            - cmdDict = commands dictionary
        """

        self.obcNumber = obcNumber    # OBC number
        self.cmdDict = cmdDict        # Command dictionary
        self.cmdLock = Lock()         # Lock to change command status in a thread-safe way
        self.newCmdEvent = Event()    # Event for a new command
        self.newCmd = ''              # New received command


###########################################################

    @property
    def SHUTDOWN(self):
        """
        Command to shutdown the OBC.
        """
        return self.cmdDict[f'SHUTDOWN_OBC{self.obcNumber}']['STATUS']

    @property
    def REBOOT(self):
        """
        Command to reboot the OBC.
        """
        return self.cmdDict[f'REBOOT_OBC{self.obcNumber}']['STATUS']

    @property
    def REBOOT_TCP(self):
        """
        Command to REBOOT the uplink.
        """
        return self.cmdDict[f'REBOOT_TCP_OBC{self.obcNumber}']['STATUS']

###########################################################

    def switchCommand(self, cmd, newValue):
        """
        Method to switch the status of one of the commands.

            Args: 
            - Command
            - Value (1/0)
        """
        # Check if the command is in the dictionary:
        if cmd in self.cmdDict.keys() and newValue in (0,1):           
            with self.cmdLock:
                # Check if the status is different:
                if self.cmdDict[cmd]['STATUS'] != newValue:
                    if newValue: 
                        # Raise the event:
                        self.newCmdEvent.set()
                        # Store command:
                        self.newCmd = cmd
                    # Change the status:
                    self.cmdDict[cmd]['STATUS'] = newValue
                    print(f' *** {cmd} STATUS SETTED TO {newValue}\n')

###################################################################################