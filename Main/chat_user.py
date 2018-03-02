class Chat_user:

    def __init__(self,name,socket,privilege):
        self.name = name
        self.socket = socket
        self.privilege = privilege
        self.status = "Available"

    def isAdmin(self):
        return "admin" == self.privilege

