import socket, time, threading, logging
import random
import string

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(threadName)s: %(message)s', datefmt='%Y.%m.%d %H:%M:%S')  # %Y.%m.%d %H:%M:%S

USED_SESSION_IDS = []

VERSION = "1.1.1"


def get_random_alphanumeric_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    result_str = ''.join((random.choice(letters_and_digits) for i in range(length)))
    return(result_str)

class enlightSession():
    ''' The main session class '''
    def __init__(self, name, password = ""):
        self.sessionId = None
        self.sessionName = name
        self.sessionPassword = password
        self.members = []
        if(self.sessionPassword == ""):
            self.passwordSet = "0"
        else:
            self.passwordSet = "1"
        self.__activ__  = False
        self.__server__ = None
        self.__server_thread__ = None
        self.allowJoin = False
    
    def initConnection(self):
        ''' Starts the main dicovery/connction method(s) '''
        global USED_SESSION_IDS
        self.sessionId = get_random_alphanumeric_string(24)
        while(self.sessionId in USED_SESSION_IDS):
            self.sessionId = get_random_alphanumeric_string(24)
        USED_SESSION_IDS.append(self.sessionId)
        self.__server__ = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.__server__.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.__activ__ = True
        self.allowJoin = True
        logging.info("Starting server thread")
        self.__server_thread__ = threading.Thread(target=self.serverMain, args=(), name="Discovery server")
        self.__server_thread__.start()

    def serverMain(self):
        logging.info("Discovery server started")
        # Set a timeout so the socket does not block
        # indefinitely when trying to receive data.
        self.__server__.settimeout(0.2)
        message = b"SESSION;" + self.sessionName.encode("utf-8") + b";" + self.sessionId.encode("utf-8") + b";"  + VERSION.encode("utf-8") + b";" + self.passwordSet.encode("utf-8") + b";" + str(len(self.members)).encode("utf-8") + b"|"

        while self.allowJoin:
            self.__server__.sendto(message, ("<broadcast>", 37020))
            logging.info("Sent discovery broadcast")
            time.sleep(1)
        logging.info("Discovery server stopped")
    




# Enable port reusage so we will be able to run multiple clients and servers on single (host, port).
# Do not use socket.SO_REUSEADDR except you using linux(kernel<3.9): goto https://stackoverflow.com/questions/14388706/how-do-so-reuseaddr-and-so-reuseport-differ for more information.
# For linux hosts all sockets that want to share the same address and port combination must belong to processes that share the same effective user ID!
# So, on linux(kernel>=3.9) you have to run multiple servers and clients under one user to share the same (host, port).
# Thanks to @stevenreddie
#   client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

# Enable broadcasting mode
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # UDP
client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

client.bind(("", 37020))





def clientMain():
    print("Client started")
    while True:
    # Thanks @seym45 for a fix
        data, addr = client.recvfrom(1024)
        data = data.decode("utf-8")
        data = data.replace("|", "")
        
        proc = data.split(";")
        # print(proc[2])
        if(proc[2] == USED_SESSION_IDS[0]):
            print("From same device")
        print(addr)
        print("received message: %s" % data)
        print(f"Rec at {time.strftime('%X')}")
    print("Client quited")

def main():
    thread = []
    ses = enlightSession("TestSession")
    ses.initConnection()
    thread.append(threading.Thread(target=clientMain, args=()))
    # thread.append(threading.Thread(target=serverMain, args=()))
    for th in thread:
        th.start()

main()
print("Quited")