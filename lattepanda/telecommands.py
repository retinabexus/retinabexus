from frozendict import frozendict
import serial

def uplink(config):

    baud    = config['PACKETS']['UPLINK']['BAUDRATE']
    port    = config['PACKETS']['UPLINK']['PORT']
    pathfb  = config['PACKETS']['FEEDBACKS']['FILE_PATH']
    uart    = serial.Serial(port, baud, pathfb)
    while not over:
        try:
            command = receive_data(uart, pathfb)
        except Exception:
            command = None
        if command is not None:
            exec_cmd(command, pathfb)




def send_data(data,ser):
    if ser.is_open:
        ser.write(data.encode())  # Send data
        print(f"Sent: {data}")

def receive_data(ser):
    if ser.is_open:
        flag = False
        while flag is False:
            data = ser.readline().decode()
            if check_cmd(data):
                flag = True
                return data
            else:
                return None

def check_cmd(data: str):
    tmp = data.split(",")
    try:
        if tmp[0] == "RET" and tmp[1] == "OBC2":
            return True
        else:
            return False
    except Exception:
        return False



    



tc_id = frozendict({
    "decommissioning" : "11",
    "reboot" : "12",
    "shutdown" : "13"
})

tc_keys = {
    "decomissioning": False,
    "reboot": False,
    "shutdown": False
}