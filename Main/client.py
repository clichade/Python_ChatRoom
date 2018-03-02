import socket
import sys
import threading
from tkinter import *

class client:
    def __init__(self):

        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a TCP/IP socket
        server_address = ('localhost', 10000)  # Connect the socket to the port where the server is listening
        print ('connecting to %s port %s' % server_address)
        self.sock.connect(server_address)
        self.close = False


        sendThread = threading.Thread(target=self.send,args=[]) #requires a tupla to pass arguments
        recieveThread = threading.Thread(target=self.recieve, args=[])  # requires a tupla to pass arguments

        sendThread.start()
        recieveThread.start()

        sendThread.join()
        print("Closing socket (1/2)")
        recieveThread.join()
        print("Closing socket (2/2)")
        self.sock.close()
        print("...socket closed")


        #self.chatWindow.mainloop()




    def send(self):

        try:
            while self.close == False:
                    # Send data
                    message = input()

                    self.sock.sendall(str.encode(message)) #encoding to send bytes
                    if message.startswith("/exit"):
                        self.close = True

        except:
            print("Error in send")


    def recieve(self):

            while self.close == False:

                    data = self.sock.recv(1024)
                    if data:
                        if data.decode() == "/exit":
                            self.close = True
                            print('Closing socket ...')
                        else:
                            print(data.decode())



if __name__ == "__main__":
    client()
