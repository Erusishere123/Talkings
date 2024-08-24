import socket
from tkinter import *
import threading
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# CLIENT CONNECTION
SERVER = "EruSISHerE.pythonanywhere.com"
PORT = 8764
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client.connect((SERVER, PORT))
    logging.debug("[DEBUG] Connected to server.")
except Exception as e:
    logging.error(f"[ERROR] Could not connect to server: {e}")

# Global username variable and room key
username = ""
current_room_key = None

def set_username():
    global username
    try:
        username = username_entry.get()
        if not username:
            logging.error("[ERROR] Username is empty")
            return

        client.sendall(username.encode('utf-8'))
        logging.debug(f"[DEBUG] Sent username: {username}")

        # Disable username entry and button
        username_entry.config(state=DISABLED)
        set_username_btn.config(state=DISABLED)

    except Exception as e:
        logging.error(f"[ERROR] Error in set_username: {e}")

def send_room_info():
    global current_room_key
    try:
        if option_var.get() == 'Create':
            client.sendall(b'C')
            room_name = room_name_entry.get()
            if not room_name:
                logging.error("[ERROR] Room name is empty")
                return

            client.sendall(room_name.encode('utf-8'))
            logging.debug(f"[DEBUG] Sent room name: {room_name}")

            current_room_key = client.recv(1024).decode('utf-8')
            if not current_room_key:
                logging.error("[ERROR] Did not receive room key")
                return
            logging.debug(f"[DEBUG] Room key received: {current_room_key}")

            # Show message frame and quit room button immediately
            create_frame.pack_forget()
            join_frame.pack_forget()
            message_frame.pack()
            quit_room_btn.pack()
            key_label.config(text=f'Room Created with key: {current_room_key}')

        elif option_var.get() == 'Join':
            client.sendall(b'J')
            key = key_entry.get()
            if not key:
                logging.error("[ERROR] Room key is empty")
                return

            client.sendall(key.encode('utf-8'))
            logging.debug(f"[DEBUG] Sent room key for joining: {key}")

            response = client.recv(1024).decode('utf-8')
            logging.debug(f"[DEBUG] Join room response: {response}")
            
            if 'JOINED ROOM' in response:
                current_room_key = key
                join_frame.pack_forget()
                create_frame.pack_forget()
                message_frame.pack()
                quit_room_btn.pack()  # Show quit room button
                status_label.config(text="Joined the room.")
            else:
                status_label.config(text=response)
                logging.debug("[DEBUG] Incorrect room key, connection remains open.")

    except Exception as e:
        logging.error(f"[ERROR] Error in send_room_info: {e}")

def add_message():
    try:
        refinedmsg = msg.get()
        if refinedmsg:
            message_to_send = f"{username}: {refinedmsg}"
            lbx.insert(END, message_to_send)
            msg.set("")
            client.sendall(f"MESSAGE {refinedmsg}".encode('utf-8'))
            logging.debug(f"[DEBUG] Sent message: {refinedmsg}")
    except Exception as e:
        logging.error(f"[ERROR] Error in add_message: {e}")

def receive_msgs():
    global username
    while True:
        try:
            received = client.recv(1024).decode('utf-8')
            if received:
                if not received.startswith(f"{username}:"):
                    lbx.insert(END, received)
                    logging.debug(f"[DEBUG] Received message: {received}")
                else:
                    logging.debug(f"[DEBUG] Ignored own message: {received}")
            else:
                logging.debug("[DEBUG] Connection closed by server.")
                break
        except Exception as e:
            logging.error(f"[ERROR] Error in receive_msgs: {e}")
            break
    client.close()

def quit_room():
    """Send request to server to leave the current room and save chat history."""
    global current_room_key
    try:
        if current_room_key:
            client.sendall(f"QUIT_ROOM {current_room_key}".encode('utf-8'))
            logging.debug("[DEBUG] Sent request to leave the room.")
            
            # Save chat history
            save_chat_history()

            # Clear the current room key and update the UI
            current_room_key = None
            message_frame.pack_forget()
            quit_room_btn.pack_forget()  # Hide quit room button
            status_label.config(text="Left the room.")
            key_label.config(text="")  # Clear the room key display
            logging.debug("[DEBUG] Successfully left the room.")
    except Exception as e:
        logging.error(f"[ERROR] Error in quit_room: {e}")

def save_chat_history():
    """Save chat history to a file."""
    try:
        if current_room_key:
            filename = f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w') as file:
                for line in lbx.get(0, END):
                    file.write(line + "\n")
            logging.debug(f"[DEBUG] Chat history saved to {filename}.")
    except Exception as e:
        logging.error(f"[ERROR] Error saving chat history: {e}")

# GUI DISPLAY
root = Tk()
root.geometry("500x577")
root.resizable(False, False)
root.title("Talkings")

# Initial setup
Label(root, text="ENTER USERNAME:", font=("Lucida Handwriting", 10, 'bold')).pack()
username_entry = Entry(root, width=50)
username_entry.pack()

set_username_btn = Button(root, text="SET USERNAME", command=lambda: threading.Thread(target=set_username).start())
set_username_btn.pack()

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

# Frames for create and join
create_frame = Frame(root)
join_frame = Frame(root)

# Create room frame
Label(create_frame, text="ENTER ROOM NAME:", font=("Lucida Handwriting", 10, 'bold')).pack()
room_name_entry = Entry(create_frame, width=50)
room_name_entry.pack()
Button(create_frame, text="Create Room", command=lambda: threading.Thread(target=send_room_info).start()).pack()

# Join room frame
Label(join_frame, text="ENTER ROOM KEY:", font=("Lucida Handwriting", 10, 'bold')).pack()
key_entry = Entry(join_frame, width=50)
key_entry.pack()
Button(join_frame, text="Join Room", command=lambda: threading.Thread(target=send_room_info).start()).pack()

# Label to show the room key
key_label = Label(root, text="", font=("Calibri", 14, 'bold'))
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

# Quit Room button
quit_room_btn = Button(root, text="QUIT ROOM", command=quit_room)
quit_room_btn.pack_forget()  # Initially hide the quit room button

# Initially show the appropriate frame based on the selection
create_frame.pack_forget()
join_frame.pack_forget()
message_frame.pack_forget()

threading.Thread(target=receive_msgs, daemon=True).start()

root.mainloop()
