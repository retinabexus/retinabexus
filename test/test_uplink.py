import socket
from time import sleep

addr = ('169.254.19.15', 5000)
BUFFERSIZE = 1024

connected = False

while True:
    # Connection loop
    while not connected:
        try:
            # Create TCP/IP socket
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Connect to GS
            print(f"\n[RETINA] Connecting ...")
            # TODO: add timeout
            client.connect(addr)
        except socket.error as error:
            print(f"\n[RETINA] Connection to GS failed")
            print(f"\n[RETINA] Error: {error}")
            print(f"\n[RETINA] New attempt, connecting to GS at {addr}")
            sleep(10)
        else:
            connected = True
            print(f"\n[RETINA] Connected to GS {addr}")
    # Receive commands if connected
    try:
        # Receive data
        print(f"\n[RETINA] Waiting for a message from GS")
        data = client.recv(BUFFERSIZE).decode("utf-8")
        ######## do something #########
        print(f"\n[RETINA] Message received from GS: {addr}")
        print(f"\n[RETINA] Message received: {data}")
        # TODO: define message structure, add some checks to the message, send an echo to GS
        if data:
            client.send(b'0')
        ######## do something #########
    except Exception as error:
        print(f"\n[RETINA] Error receiving message: {error}")
        print(f"\n[RETINA] Trying to restore connection")
        # Reset connection status
        connected = False
    
