import socket
import select
from server_utils import UsersDB, ScoresDB, Message, Sorting_Numbers, Chat
import threading
import json

def handle_client(client_socket):
    try:
        while True:
            data = client_socket.recv(1024)
            client_message = data.decode('utf-8')
            if not data or client_message == "exit":
                break
            print(f"Received data: {data.decode('utf-8')}")

    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        client_exit(client_socket)


def client_exit(client_socket):
    client_socket.close()
    print("Client has disconnected")





class Server:
    # handles the multiuser server
    def __init__(self, host, port):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.current_usernames = []
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        self.message = Message()
        self.clients = [self.server_socket]
        self.clients_names = {}
        self.wfc = []
        self.database = UsersDB()
        self.scores = ScoresDB()
        self.sorting_numbers = Sorting_Numbers()
        self.messages = []

        # Initialize rlist, wlist, and xlist
        self.rlist = []
        self.wlist = []
        self.xlist = []

    def start(self):
        print(f"Server is listening on {self.server_socket.getsockname()}")

        while True:
            # Copy the clients list to rlist for monitoring read events
            self.rlist = list(self.clients)
            rlist, _, _ = select.select(self.rlist, self.wlist, self.xlist)

            for sock in rlist:
                if sock == self.server_socket:
                    # New connection, accept it
                    client_socket, client_address = self.server_socket.accept()
                    self.clients.append(client_socket)
                    print(f"New connection from {client_address}")
                else:
                    # Handle data from an existing client
                    try:
                        data = sock.recv(1024)
                        temp = list(self.message.decode_json(data))
                        self.messages.append(temp)
                        # print("Client: ", temp)
                        result_msg = self.handle_messages()
                        if (result_msg[0] == "login" or result_msg[0] == "signup") and result_msg[1] == "success":
                            self.clients_names[result_msg[2]] = sock
                        print(self.clients_names)
                        # print("Server: ", str(result_msg))
                        result_json_msg = self.message.encode_json(result_msg)
                        sock.send(result_json_msg)
                    except:
                        for username in self.clients_names:
                            if self.clients_names[username] == sock:
                                self.clients_names.pop(username)
                                print("Done ! Boss")
                                break
                        self.clients.remove(sock)
                        print("Server: Client has been disconnected")
                    

    def handle_messages(self):
        for msg in self.messages:
            if type(msg) is list:
                if msg[0] == "login":
                    if self.database.try_login(msg[1], msg[2]):
                        username = msg[1]
                        self.messages.remove(msg)
                        return ["login", "success", username] # msg[1] -> username
                    else:
                        if self.database.check_user_registered(msg[1]):
                            self.database.check_user_registered(msg[1])
                        self.messages.remove(msg)
                        return ["login", "error", self.database.check_user_registered(msg[1])]
                    
                if msg[0] == "signup":
                    if not self.database.check_user_registered(msg[1]):
                        self.database.insert_user(msg[1], msg[2])
                        print("new user successfully registered")
                        username = msg[1]
                        self.messages.remove(msg)
                        return ["signup", "success", username] # [2] -> username
                    else:
                        # the username is already exists
                        print("This username is already exists")
                        self.messages.remove(msg)
                        return ["signup", "error", msg[1]]
                    
                if msg[0] == "game":

                    if msg[1] == "sorting numbers":
                        if msg[2] == "start":
                            numbers = self.sorting_numbers.generate_numbers()
                            self.messages.remove(msg)
                            return ["game", "sorting numbers", numbers]
                        
                        if msg[2] == "check sorted numbers":
                            if int(msg[3]) == int(''.join(map(str, sorted(self.sorting_numbers.numbers_to_sort)))):
                                self.messages.remove(msg)
                                return ["game", "sorting numbers", "success", self.scores.getMean(msg[4])]
                            self.messages.remove(msg)
                            return ["game", "sorting numbers", "fail"]
                        
                        if msg[2] == "set score":
                            time = msg[4]
                            score = 300 - time
                            self.scores.insert_score(msg[3], "sorting numbers", score)
                            self.messages.remove(msg)
                            return ["game", "sorting numbers", "successfully set score", self.scores.getMean(msg[3]), score]
                            
                    if msg[1] == "chat":
                        if msg[2] == "join":
                            if self.wfc == []:
                                self.wfc.append(msg[3])
                                return ["game", "chat", "waiting for player"]
                            else:
                                self.clients_names[self.wfc[0]].send(self.message.encode_json(["game", "chat", "found"]))
                                self.wfc = []

                    '''
                    if msg[1] == "chat":
                        if msg[2] == "cancel":
                            self.chat.waiting_client = None
                            self.messages.remove(msg)
                            return ["cancelling chat"]
                        if msg[2] == "join":
                            if self.chat.waiting_client is None:
                                self.chat.waiting_client = msg[3]
                                self.messages.remove(msg)
                                return ["game", "chat", "waiting"]
                            else:
                                self.create_chat(self.chat.waiting_client, msg[3])
                                self.chat.waiting_client = None
                                self.messages.remove(msg)
                                return ["game", "chat", "connected"]
'''



class ChatServer:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("127.0.0.1", 5555))
        self.server_socket.listen(2)

        self.connections = []

    def accept_connections(self):
        while True:
            connection, address = self.server_socket.accept()
            self.connections.append(connection)

            if len(self.connections) == 2:
                self.start_chat()

                threading.Thread(target=self.receive_messages, args=(0,)).start()
                threading.Thread(target=self.receive_messages, args=(1,)).start()

    def start_chat(self):
        print("Both players joined. Starting chat.")

    def receive_messages(self, player_index):
        connection = self.connections[player_index]
        while True:
            try:
                message = connection.recv(1024).decode('utf-8')
                if not message:
                    break
                self.broadcast_message(f"Player {player_index + 1}: {message}")
            except Exception as e:
                break

    def broadcast_message(self, message):
        for connection in self.connections:
            connection.send(message.encode('utf-8'))

"""
if __name__ == "__main__":
    chat_server = ChatServer()
    chat_server.accept_connections()"""



if __name__ == "__main__":
    # Create and start the server
    server = Server('127.0.0.1', 12345)
    server.start()