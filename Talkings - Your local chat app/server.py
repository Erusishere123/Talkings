import socket
import threading
import random
import string
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

SERVER = "localhost"
PORT = 8764
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((SERVER, PORT))
server.listen()

rooms = {}  # Room structure: {'key': {'name': 'room_name', 'clients': [conn1, conn2]}}
lock = threading.Lock()

def generate_key(length=6):
    """Generate a random key for room identification."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def handle_clients(conn, addr):
    key = None
    username = None
    try:
        # Send initial prompt and receive username
        conn.sendall(b'ENTER USERNAME:')
        username = conn.recv(1024).decode('utf-8')

        # Receive command for room creation or joining
        conn.sendall(b'CREATE or JOIN ROOM (C/J):')
        command = conn.recv(1024).decode('utf-8').strip().upper()
        logging.debug(f"[DEBUG] Received command: {command}")

        if command == 'C':
            # Handle room creation
            conn.sendall(b'ENTER ROOM NAME:')
            room_name = conn.recv(1024).decode('utf-8')
            key = generate_key()
            with lock:
                rooms[key] = {'name': room_name, 'clients': [conn], 'usernames': [username]}
            logging.debug(f"[DEBUG] Room created with key: {key}")
            conn.sendall(key.encode('utf-8'))  # Send the key immediately after creation
        
        elif command == 'J':
            # Handle joining an existing room
            conn.sendall(b'ENTER ROOM KEY:')
            key = conn.recv(1024).decode('utf-8')
            logging.debug(f"[DEBUG] Received room key: {key}")

            with lock:
                room = rooms.get(key)
                if room:
                    room['clients'].append(conn)
                    room['usernames'].append(username)
                    conn.sendall(f'JOINED ROOM: {room["name"]}'.encode('utf-8'))
                    logging.debug(f"[DEBUG] Client joined room: {room['name']}")
                else:
                    conn.sendall(b'INVALID ROOM KEY')
                    conn.close()
                    return

        # Receive and broadcast messages
        while True:
            received = conn.recv(1024).decode('utf-8')
            if not received:
                break
            if 'MESSAGE' in received:
                _, message = received.split(' ', 1)
                formatted_message = f"{username}: {message}"
                broadcast(formatted_message, key)
                
    except Exception as e:
        logging.error(f"ERROR : {e}")
    finally:
        # Cleanup when client disconnects
        with lock:
            if key in rooms:
                index = rooms[key]['clients'].index(conn)
                rooms[key]['clients'].remove(conn)
                rooms[key]['usernames'].pop(index)
                if not rooms[key]['clients']:
                    del rooms[key]
        conn.close()

def broadcast(message, key):
    """Broadcast a message to all clients in the specified room."""
    with lock:
        room = rooms.get(key)
        if room:
            for client in room['clients']:
                try:
                    client.sendall(message.encode('utf-8'))
                except Exception as e:
                    logging.error(f"ERROR : {e}")
                    room['clients'].remove(client)
                    if not room['clients']:
                        del rooms[key]

while True:
    conn, addr = server.accept()
    logging.debug(f"Accepted connection from {addr}")
    thread = threading.Thread(target=handle_clients, args=[conn, addr])
    thread.start()
