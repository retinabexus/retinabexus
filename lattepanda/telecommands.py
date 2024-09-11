import serial
import time
import os
from utils      import log_message, write_log
import yaml


def send_data(data,ser):
    if ser.is_open:
        ser.write(data.encode())  # Send data
        print(f"Sent: {data}")

def receive_data(ser):
    if ser.is_open and ser.in_waiting > 0:
        flag = False
        while flag is False:
            data = ser.readline().decode('utf-8')
            if check_cmd(data):
                flag = True
                return data
            else:
                return None
    else:
        return None

def check_cmd(data: str):
    tmp = data.split("\n")
    try:
        if tmp[0] == 'REBOOT_OBC2':
            return True
        else:
            return False
    except Exception:
        return False

def exec_cmd(commands):
    reboot = commands['COMMANDS']['INNER']['REBOOT']
    cmd = 'sudo %s'% reboot
    os.system(cmd)
    
def uplink(serd, config):
    pathfb   = config['PACKETS']['FEEDBACKS']['FILE_PATH']
    try:
        message = "Started listening"
        print(message)
        write_log(log_message(message), pathfb)
        while True:
            data = receive_data(serd)
            if data is not None:
                print(data)
            else:
                time.sleep(0.2)
    except Exception:
        message = "Something wrong occurred while listening"
        print(message)
        write_log(log_message(message), pathfb)
        time.sleep(10)

if __name__ == '__main__':
    # Read configuration file
    with open('/home/retina/Desktop/retinabexus/lattepanda/Input/config.yaml','r') as d: config = yaml.full_load(d) 
    serd = serial.Serial(baudrate = 115200, port = '/dev/ttyUSB1')

    uplink(serd,config)