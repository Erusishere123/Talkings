import socket
from tkinter import *
import threading
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# CLIENT CONNECTION
SERVER = "rattle-hail-antarctopelta.glitch.me/"
PORT = 8764  # Ensure this matches the port your server is listening on

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def connect_to_server():
    try:
        client.connect((SERVER, PORT))
        logging.debug("[DEBUG] Connected to server.")
        receive_msgs()  # Start receiving messages
    except Exception as e:
        logging.error(f"[ERROR] Could not connect to server: {e}")

def send_username():
    try:
        username = username_entry.get()
        client.sendall(username.encode('utf-8'))
        logging.debug(f"[DEBUG] Sent username: {username}")

        if option_var.get() == 'Create':
            client.sendall(b'C')
            room_name = room_name_entry.get()
            client.sendall(room_name.encode('utf-8'))
            logging.debug(f"[DEBUG] Sent room name: {room_name}")

            # Receive the key for the created room
            key = client.recv(1024).decode('utf-8')
            logging.debug(f"[DEBUG] Room key received: {key}")

            # Update the key label on the main thread
            root.after(0, lambda: key_label.config(text=f'Room Created with key: {key}'))
            create_frame.pack_forget()
            message_frame.pack()

        elif option_var.get() == 'Join':
            client.sendall(b'J')
            key = key_entry.get()
            client.sendall(key.encode('utf-8'))
            logging.debug(f"[DEBUG] Sent room key for joining: {key}")

            # Receive the response after trying to join the room
            response = client.recv(1024).decode('utf-8')
            logging.debug(f"[DEBUG] Join room response: {response}")

            status_label.config(text=response)
            if 'JOINED ROOM' in response:
                join_frame.pack_forget()
                message_frame.pack()

    except Exception as e:
        logging.error(f"[ERROR] Error in send_username: {e}")

def add_message():
    try:
        refinedmsg = msg.get()
        lbx.insert(END, f"YOU: {refinedmsg}")
        msg.set("")
        client.sendall(f"MESSAGE {refinedmsg}".encode('utf-8'))
        logging.debug(f"[DEBUG] Sent message: {refinedmsg}")
    except Exception as e:
        logging.error(f"[ERROR] Error in add_message: {e}")

def receive_msgs():
    while True:
        try:
            received = client.recv(1024).decode('utf-8')
            if received:
                username, message = received.split(': ', 1)
                if username != username_entry.get():
                    lbx.insert(END, f"{username}: {message}")
                    logging.debug(f"[DEBUG] Received message: {received}")
            else:
                logging.debug("[DEBUG] Connection closed by server.")
                break
        except Exception as e:
            logging.error(f"[ERROR] Error in receive_msgs: {e}")
            break
    client.close()

# GUI DISPLAY
root = Tk()
root.geometry("500x500")
root.resizable(False, False)
root.title("Chat Rooms")

# Initial setup
Label(root, text="ENTER USERNAME:", font=("Lucida Handwriting", 10, 'bold')).pack()
username_entry = Entry(root, width=50)
username_entry.pack()

# Options for creating or joining rooms
option_var = StringVar(value='Create')
Radiobutton(root, text="Create Room", variable=option_var, value='Create', command=lambda: show_create_room()).pack()
Radiobutton(root, text="Join Room", variable=option_var, value='Join', command=lambda: show_join_room()).pack()

def show_create_room():
    join_frame.pack_forget()
    create_frame.pack()

def show_join_room():
    create_frame.pack_forget()
    join_frame.pack()

def quit_room():
    client.sendall(b'QUIT')
    message_frame.pack_forget()
    create_frame.pack_forget()
    join_frame.pack_forget()
    username_entry.pack()

# Frames for create and join
create_frame = Frame(root)
join_frame = Frame(root)

# Create room frame
Label(create_frame, text="ENTER ROOM NAME:", font=("Lucida Handwriting", 10, 'bold')).pack()
room_name_entry = Entry(create_frame, width=50)
room_name_entry.pack()
Button(create_frame, text="Create Room", command=lambda: threading.Thread(target=send_username).start()).pack()

# Join room frame
Label(join_frame, text="ENTER ROOM KEY:", font=("Lucida Handwriting", 10, 'bold')).pack()
key_entry = Entry(join_frame, width=50)
key_entry.pack()
Button(join_frame, text="Join Room", command=lambda: threading.Thread(target=send_username).start()).pack()

key_label = Label(root, text="", font=("Lucida Handwriting", 10, 'bold'))
key_label.pack()

status_label = Label(root, text="", font=("Lucida Handwriting", 10, 'bold'))
status_label.pack()

message_frame = Frame(root)
Label(message_frame, text="HISTORY", font=("Lucida Handwriting", 18, 'bold'), height=2).pack()
lbx = Listbox(message_frame, width=75, height=17)
lbx.pack()
msg = StringVar()
MSG = Entry(message_frame, width=50, textvariable=msg)
MSG.pack()
sendbtn = Button(message_frame, text="SEND", command=add_message)
sendbtn.pack()

quitbtn = Button(message_frame, text="QUIT ROOM", command=quit_room)
quitbtn.pack()

# Initially show the appropriate frame based on the selection
create_frame.pack_forget()
join_frame.pack_forget()
message_frame.pack_forget()

# Connect to server
threading.Thread(target=connect_to_server, daemon=True).start()

root.mainloop()
