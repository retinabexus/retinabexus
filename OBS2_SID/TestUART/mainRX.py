import serial
import time

ser = serial.Serial(
    port = '/dev/ttyS0',
    baudrate = 9600,
    timeout = 1
)

while True:
    if ser.in_waiting > 0:
        data = ser.readline().decode('utf-8').rstrip()
        print(f"Received: {data}")
