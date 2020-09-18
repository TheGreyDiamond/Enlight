'''
session.py
===============================
The session support for Enlight
'''

import socket, time, threading, logging
import random
import string

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(threadName)s: %(message)s', datefmt='%Y.%m.%d %H:%M:%S')  # %Y.%m.%d %H:%M:%S

USED_SESSION_IDS = []

VERSION = "1.1.2"

## Role defs
HOST = 0
USER = 1
ADMIN = 2
VALID_ROLES = [HOST, USER, ADMIN]

def get_local_ip(no = 0):
    """
    Gets the local ip address

    :int no: ID of the ip adress
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ipAddr = s.getsockname()[no]
    s.close()
    return(ipAddr)

def get_random_alphanumeric_string(length):
    """
    Returns a random alphanumeric string

    :int length: The length of the output string
    """
    letters_and_digits = string.ascii_letters + string.digits
    result_str = ''.join((random.choice(letters_and_digits) for i in range(length)))
    return(result_str)

class enlightSession():
    """
    The main session class

    :string name: The session name (not needed)
    :string role: The role of the local instance (defaults to HOST, can be HOST or USER)
    """
    def __init__(self, name = "", role = HOST, passcode = ""):
        self.sessionName = name
        self.__activ__  = False

        self.__my_ip__ = get_local_ip()
        logging.info("My IP is: " + self.__my_ip__)

        ## For HOST role
        self.sessionId = None
        self.__server__ = None
        self.__server_thread__ = None
        self.sessionpasscode = passcode
        self.members = []
        self.allowJoin = False
        self.__direct_socket__ = None
        self.__direct_thread__ = None

        ## For USER and ADMIN role
        self.sessionId = None
        self.__client__ = None
        self.__client_thread__ = None
        self.allOnlineSessions = {}
        self.connected = False
        self.__direct_socket__ = None
        
        self.__role__ = role

        if(self.sessionpasscode == ""):
            self.passcodeSet = "0"
        else:
            self.passcodeSet = "1"

        if(self.__role__ not in VALID_ROLES):
            self.__role__ = HOST
            logging.warning("No vaild session role was set, using HOST as default")
        
        if(self.__role__ == HOST and name == ""):
            logging.warning("Role is set to HOST, but no session name was given.")
            self.sessionName = "Unnamed session"
        
    
    def initConnection(self):
        """
        Starts the main dicovery/connction method(s)
        """
        global USED_SESSION_IDS
        if(self.__role__ == HOST):
            self.sessionId = get_random_alphanumeric_string(24)
            while(self.sessionId in USED_SESSION_IDS):
                self.sessionId = get_random_alphanumeric_string(24)
            logging.info("My session id is " + self.sessionId)
            USED_SESSION_IDS.append(self.sessionId)
            self.__server__ = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.__server__.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.__activ__ = True
            self.allowJoin = True
            logging.info("Starting server thread")
            self.__server_thread__ = threading.Thread(target=self.serverMain, args=(), name="Discovery server")
            self.__server_thread__.start()

            self.__direct_socket__ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # self.__direct_socket__.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            # self.__direct_socket__.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.__direct_socket__.bind(("", 5589))
            self.__direct_thread__ = threading.Thread(target=self.lightSearcherMain, args=(), name="Inbound session server")
            self.__direct_thread__.start()

        elif(self.__role__ == USER or self.__role__ == ADMIN):
            self.__client__ = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)#, socket.IPPROTO_UDP)  # UDP
            self.__client__.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.__client__.bind(("", 37020))

            logging.info("Starting lighthouse thread")
            self.__activ__  = True
            self.__direct_socket__ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.__direct_socket__.bind(("", 5589))
            self.__client_thread__ = threading.Thread(target=self.lighthouseMain, args=(), name="Lighthouse server")
            self.__client_thread__.start()
            self.__direct_thread__ = threading.Thread(target=self.lightSearcherDirectMain, args=(), name="Inbound session direct server")
            self.__direct_thread__.start()
            self.__trying_to_connect__ = False
            

    def lightSearcherMain(self):
        """
        The main thread for clients to connect
        """
        logging.info("Inbound connection handler started")
        self.__direct_socket__.listen()
        while self.allowJoin: 
            try:
                conn, addr = self.__direct_socket__.accept()
                data = conn.recv(1024)
                conn.sendall(b"CONNECTION INT OK")
                logging.info("Got inbound connection with data: " + str(data) + " from " + str(addr))
            except OSError:
                logging.warning("Client socket, failure. Session maybe not avaiable anymore?")
            
        logging.info("Inbound connection handler stopped")

    def lightSearcherDirectMain(self):
        """
        The Handler for direct comuncation between HOST and USER
        """
        while self.allowJoin: 
            try:
                conn, addr = self.__direct_socket__.accept()
                data = conn.recv(1024)
                if(self.__trying_to_connect__ != False):
                    conn.sendall(b"ACK")
                logging.info("Got inbound connection with data: " + str(data) + " from " + str(addr))
            except OSError:
                logging.warning("Client socket, failure. Session maybe not avaiable anymore?")

    def lighthouseMain(self):
        """
        The main thread for searching/finding sessions
        """
        while self.__activ__:
            try:
                data, addr = self.__client__.recvfrom(1024)
            except OSError:
                logging.warning("Client socket, failure. Session maybe not avaiable anymore?")
            else:
                data = data.decode("utf-8")
                data = data.replace("|", "")
                proc = data.split(";")

                logging.info("Got broadcast from " + str(addr) + " with data " + str(proc))
                if(proc[3] != VERSION): #if(proc[3] == VERSION):
                    logging.warning("Software versions are not compatible. ABORT")
                else:
                    ## More data handling
                    if(proc[2] not in self.allOnlineSessions):
                        proc.append(addr)
                        self.allOnlineSessions[proc[2]] = proc
                        logging.info("Found new session named " + proc[1])

    def clearAllSessions(self):
        """
        Clears all discoverd sessions 
        """
        if(self.__role__ != HOST):
            logging.info("Clearing all know session")
            self.allOnlineSessions = {}

    def serverMain(self):
        """
        Main Discovery server
        """
        logging.info("Discovery server started")
        # Set a timeout so the socket does not block
        # indefinitely when trying to receive data.
        self.__server__.settimeout(0.2)
        message = b"SESSION;" + self.sessionName.encode("utf-8") + b";" + self.sessionId.encode("utf-8") + b";"  + VERSION.encode("utf-8") + b";" + self.passcodeSet.encode("utf-8") + b";" + str(len(self.members)).encode("utf-8") + b"|"

        while self.allowJoin:
            ipChoped = get_local_ip().split(".")
            ipWithBroadEnding = ipChoped[0] + "." + ipChoped[1] + "." + ipChoped[2] + ".255"
            self.__server__.sendto(message, (ipWithBroadEnding, 37020))    # <broadcast>  192.168.178.60 255.255.255.255

            logging.info("Sent discovery broadcast")
            time.sleep(1)
        logging.info("Discovery server stopped")

    def getSessionMembers(self):
        """
        Get all session members
        :return: Returns a list of all members
        """
        return(self.members)
    
    def getSessionId(self):
        ''' Get the local session id '''
        return(self.sessionId)

    def join(self, sessionID):
        ''' Join a remote session '''
        if(not self.connected):
            try:
                data = self.allOnlineSessions[sessionID]
            except KeyError:
                logging.error("an unknow/undiscorvered session ID was given")
                return(-2)
            else:
                try:
                   # print((data[len(data)-1][0], 5589))
                    ## Try to open a socket to the ip/port
                    self.__direct_socket__ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # UDP
                    self.__direct_socket__.connect((data[len(data)-1][0], 5589))
                    
                    self.__direct_socket__.sendall(b'CONNECT')
                    self.__trying_to_connect__ = sessionID
                    logging.info("Sent JOIN intent to session host")
                except ConnectionRefusedError:
                    logging.warning("Connection refused by session host")
                    return(-1)
                else:
                    return(1)
        else:
            logging.warning("join was called, while there is a session activ")
            return(-2)

    def leave(self):
        ''' Leaves the session, will take at least two seconds '''
        if(self.__role__ == USER or self.__role__ == ADMIN):
            ## TODO: Send leave command to host
            self.__activ__  = False
            time.sleep(2)
            self.__client__.shutdown(socket.SHUT_RDWR)
            self.__client__.close()
            logging.info("Closed Lighthouse port")
        else:
            logging.warning("leave was called, without the role set to USER or ADMIN. Did you mean .stopSession?")

    def stopSession(self):
        ''' Stops the session as a HOST '''
        if(self.__role__ == HOST):
            self.allowJoin = False
            self.__activ__ = False
            # TODO: Kick all users
            self.members = []
            self.__server_thread__ = None
            self.__server__.shutdown(socket.SHUT_RDWR)
            self.__server__.close()
            #self.__direct_socket__.shutdown(socket.SHUT_RDWR)
            self.__direct_socket__.close()
            logging.info("Closed Discovery server port")
        else:
            logging.warning("stopSession was called, without the role set to HOST. Did you mean .leave?")



def testModule():
    testSession = enlightSession("TestSession", role = HOST)
    userSession = enlightSession("myLocalSession", role = USER)
    userSession.initConnection()
    testSession.initConnection()
    time.sleep(1)
    userSession.join(testSession.getSessionId())
    time.sleep(8)
    testSession.stopSession()
    userSession.leave()

def testOnlyServer():
    testSession = enlightSession("TestSession", role = HOST)
    testSession.initConnection()
    time.sleep(30)
    testSession.stopSession()

if __name__ == "__main__":
    testOnlyServer()
 