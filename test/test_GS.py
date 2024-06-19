import socket
import threading
from time import sleep

GS_ADDRESS = '169.254.19.15' 
GS_PORT = 123  

def handle_client(client):

    print(f"\n[GS] Connected to client {client.getpeername()}")

    while True:
        try:
            # Send a message to RETINA
            available = True
            while available:
                message = input()
                client.sendall(f"{message}\n".encode())
                available = False
            # Receive data from the client
            data = client.recv(1024).decode()
            if not data:
                print(f"\n[GS] Client {client.getpeername()} disconnected")
                break

            print(f"Received from RETINA {client.getpeername()}: {data}")

            # Echo back the received message
            client.sendall(data.encode())
            available = True
        except Exception as e:
            print(f"\n[GS] Error handling client: {e}")
            break

    # Close the client socket
    client.close()

def start_server():
    try:
        # Create a socket
        gs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Bind the socket to the address and port
        gs.bind((GS_ADDRESS, GS_PORT))
        # Listen for incoming connections
        gs.listen(5)
        print(f"\n[GS] Server listening on {GS_ADDRESS}:{GS_PORT}")

        # Main loop for accepting incoming connections
        while True:
            # Accept a client connection
            client_socket, client_address = gs.accept() # Program stops here waiting for a connection from a client
            # Handle the client in a separate thread
            client_thread = threading.Thread(target=handle_client, args=(client_socket,))
            client_thread.start()
            while True:
                print('\nSono qui mentre eseguo il thread')
                sleep(5)
    except Exception as e:
        print(f"[GS] Error starting server: {e}")
    finally:
        # Close the server socket
        gs.close()

if __name__ == "__main__":
    start_server()
