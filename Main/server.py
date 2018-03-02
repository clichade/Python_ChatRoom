import socket
import sys
import threading
import select
import json
from Main.chat_user import Chat_user
import colorama
from colorama import Fore, Back, Style

"""
Fore: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
Back: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
Style: DIM, NORMAL, BRIGHT, RESET_ALL
"""
class server:

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create a TCP/IP socket
        self.server_address = ('localhost', 10000) # Address tuple (ip,port)
        print('starting up on %s port %s' % self.server_address)
        self.sock.bind(self.server_address)  # Bind the socket to the port

        self.connected_users = [] #list of chat_users

        self.writingLock = threading.Lock() #lock for saving data

        with open('clients_database.json','r') as clientsFile: #load registered users into registered users
            self.registered_users = json.load(clientsFile) #dictionary with all the users and their passwords


    """
    2 Main functions:
        1. Starts listening to possible clients 
        2. Manage the messages in between clients
    """
    def start(self):
        threading._start_new_thread(self.listen, ()) #Listen to possible connections from clients
        self.broadcast()



    """
    Recieves all the messages from the connected users and retransmit them to all users
    TODO: cambiar todo el sistema de 
    """
    # TODO: cambiar todo el sistema de usuarios porque esto es ilegible
    def broadcast(self):
        # Receive the data in small chunks and retransmit it
        while True:
            for user in self.connected_users:  # user is a tuple (username,socket)
                user.socket.setblocking(0)
                ready = select.select([user.socket], [], [], 0.1)  # wait until data is available or the time out passed
                if ready[0]: #if there is a message
                    data = user.socket.recv(1024)
                    data = data.decode() # the message will be decoded to theck if it´s something special first
                    if data.startswith("/"):
                        if data.startswith("/userlist"):
                            self.command_userlist(user)

                        elif data.startswith("/setbusy"):
                            self.command_setbusy(user)

                        elif data.startswith("/setavailable"):
                            self.command_setavailable(user)

                        elif data.startswith("/help"):
                            self.command_help(user)

                        elif data.startswith("/pm"):
                            self.command_pm(user, data)

                        elif data.startswith("/exit"):
                            self.command_exit(user)

                        elif data.startswith("/ban"):
                            self.command_ban(user, data)

                        elif data.startswith("/reset"):
                            self.command_reset(user)

                        else:
                            user.socket.sendall(self.encode_notification("Nonexistent command, send /help to see a list"
                                                                         " of available commands."))

                    else: #send to all available users
                        data = user.name + ": " + data #update the data with the users username
                        print(data)
                        self.send_all(str.encode(data))

    """ 
    Send the user a list of the connected users and their status
    """
    def command_userlist(self,user):
        print("Userlist requested by %s" % user.name)
        user_string = "Users in the chat %d: \n" % len(self.connected_users)
        for u in self.connected_users:
            user_string = user_string + "\t%s : %s - %s \n" % (u.name,u.status,u.privilege)

        user.socket.sendall(str.encode(user_string))


    """
    Sets the user status to busy
    """
    def command_setbusy(self,user):
        user.status = "Busy"
        user.socket.sendall(self.encode_notification("SERVER: Your status has been changed to Busy"))
        print("user %s has changed his/her status to Busy" % user.name)

    """
    Sets the user status to available
    """
    def command_setavailable(self,user):
        user.status = "Available"
        user.socket.sendall(self.encode_notification("SERVER: Your status has been changed to Available"))
        print("user %s has changed his/her status to Available" % user.name)

    def command_exit(self,user):
        self.connected_users.remove(user)
        user.socket.sendall(str.encode("/exit"))
        self.send_all(self.encode_notification("User %s left the chat" % user.name))
        print("Connection closed with", user.name)


    def command_help(self,user):
        help_string = "SERVER: This is a list of the commands offered by the chat \n" \
                    "\t/userlist : Shows a list of the online users and their status \n" \
                    "\t/setbusy : Changes your status to Busy, that means you won´t receive messages from the main chat \n" \
                    "\t/setavailable : Changes your status to Available, that means you won´t receive messages from the main chat \n" \
                    "\t/help : shows the list of commands with a brief description \n " \
                    "\t/pm user message : sends to the desired user a private message \n" \
                    "\t/exit : you exit the chat \n" \
                    "\t*ADMIN ONLY: /ban user : the user is banned from the chat \n" \
                    "\t*ADMIN ONLY: /reset : the server is restored to an empty state \n"

        print("Help requested by %s" % user.name)
        user.socket.sendall(str.encode(help_string))

    """Send a private message in magenta"""
    def command_pm(self,user,data):
        words = str.split(data)
        names = [user.name for user in self.connected_users]
        if words[1] in names:
            destination_user = [user for user in self.connected_users if user.name == words[1]]
            print(data)
            user.socket.sendall(str.encode(Fore.MAGENTA + "PM to %s: %s "
                                           %(destination_user[0].name," ".join(str(x) for x in words[2:]) + Style.RESET_ALL)))
            destination_user[0].socket.sendall(str.encode((Fore.MAGENTA +"PM from %s: %s "
                                                          %(user.name," ".join(str(x) for x in words[2:]) + Style.RESET_ALL))))

        else:
            user.socket.sendall(self.encode_notification("SERVER: Invalid user for private message"))
            print("Invalid user for private message")

    def send_all(self,message):
        [c.socket.sendall(message) for c in self.connected_users if c.status == "Available"]

    def command_reset(self, user):
        if user.isAdmin():
            self.send_all(self.encode_warning("╔═══════════════════════════╗\n"
                                              "  THE SERVER WILL RESET\n"
                                              "╚═══════════════════════════╝\n"))
            self.send_all(str.encode("/exit"))
            self.connected_users = []

        else:
            user.socket.sendall(
            self.encode_notification("SERVER: you don´t have the privileges to perform this action"))



    def command_ban(self,user,data):
        if user.isAdmin():
            words = str.split(data)
            names = [user.name for user in self.connected_users]
            if words[1] in names:
                destination_user = [user for user in self.connected_users if user.name == words[1]]
                self.send_all(self.encode_warning("The user %s has been banned" % destination_user[0].name))
                destination_user[0].socket.sendall(str.encode("/exit"))
                self.connected_users.remove(destination_user[0])


            else:
                user.socket.sendall(self.encode_notification("SERVER: Invalid user for ban"))
                print("Invalid user for ban")

        else:
            user.socket.sendall(self.encode_notification("SERVER: you don´t have the privileges to perform this action"))



    #todo este trhead no finaliza
    """
    Listens possible connections of the clients, for each client what attemps to connect launches a
    thread do manage it individualy,
    """
    def listen(self):
        self.sock.listen(20)#max number of clients 20

        print('<SERVER WAITING FOR CONNECTIONS>')

        while True:
            connection, client_address = self.sock.accept()
            print('connection from', client_address)

            threading._start_new_thread(self.manageClient, (connection,))

        print("<SERVER SHUT DOWN>")


    """ 
    When the client connects with the server access this method wich manages the register , login process
    
        The method requires:
            Connection = Socket of the clients         
    """
    def manageClient(self,connection):

            connection.sendall(str.encode("SERVER: Select and option 1.Log In, 2.Register, 3.Exit"))

            while True:
                data = connection.recv(1024)
                if data.decode() == "1":
                    self.logIn(connection)
                    break
                elif data.decode() == "2":
                    self.register(connection)
                    break
                elif data.decode() == "3":
                    print("Closing connection with an unknown user")
                    #todo hay que cerrar en el otro lado también
                    connection.sendall(self.encode_notification("SERVER: Connection closed with the server"))
                    connection.close()
                    break
                else:
                    connection.sendall(str.encode("SERVER: Wrong input, try again please"))



    def logIn(self,connection):

        connection.sendall(str.encode("SERVER: Log In "))

        while True:
            connection.sendall(str.encode("SERVER: Insert Username"))
            user = 0
            while not user:
                user = connection.recv(1024)

            connection.sendall(str.encode("SERVER: Insert password:"))

            password = 0
            while not password:
                password = connection.recv(1024)

            print(self.registered_users)
            userlist = self.registered_users["users"]
            if user.decode() in [u["name"] for u in userlist]:
                userDictionary = [u for u in userlist if u["name"] == user.decode()][0]

                if userDictionary["password"] == password.decode():
                    self.connected_users.append(Chat_user(userDictionary["name"],connection,userDictionary["privilege"]))#add a chat_user to connected users
                    self.send_all(self.encode_notification("SERVER: User %s joined the chat" % user.decode()))
                    #   notify all other users
                    break

                else:
                    connection.sendall(self.encode_notification("SERVER: Wrong username or password"))

            else:
                connection.sendall(self.encode_notification("SERVER: Wrong username or password"))


    def encode_notification(self, message):
        return str.encode(Fore.YELLOW + message + Style.RESET_ALL)

    def encode_warning(self, message):
        return str.encode(Fore.RED + message + Style.RESET_ALL)


    def register(self,connection):
        while True:
            connection.sendall(str.encode("SERVER: Register "))
            connection.sendall(str.encode("SERVER: Create an username"))
            user = 0
            while not user:
                user = connection.recv(1024).decode()

            connection.sendall(str.encode("SERVER: Create a password for the new user"))

            password = 0
            while not password:
                password = connection.recv(1024).decode()

            connection.sendall(str.encode("SERVER: Is admin? (y/n)"))

            isAdmin = 0
            while not isAdmin:
                isAdmin = connection.recv(1024).decode()
                if isAdmin == "y":
                    isAdmin = "admin"

                elif isAdmin == "n":
                    isAdmin = "regular"

                else:
                    isAdmin = 0
                    connection.sendall(str.encode("SERVER: Wrong input, try again"))


            print(self.registered_users)
            userlist = self.registered_users["users"]
            if user not in [u["name"] for u in userlist]:

                try:
                    self.writingLock.acquire()
                    self.registered_users["users"].append({"name": user,
                                                            "password": password,
                                                            "privilege": isAdmin})

                    with open("clients_database.json",'w') as clientsFile:
                        json.dump(self.registered_users,clientsFile)

                    connection.sendall(self.encode_notification("SERVER: Your user name has been registered"))

                    with open('clients_database.json', 'r') as clientsFile:  # load registered users into registered users
                        self.registered_users = json.load(clientsFile)  # dictionary with all the users and their passwords
                    self.logIn(connection)

                finally:
                    self.writingLock.release()
                    break

            else:
                connection.sendall(self.encode_notification("SERVER: This user already exists, try again"))


if __name__ == "__main__":
    chat_server = server()
    chat_server.start()