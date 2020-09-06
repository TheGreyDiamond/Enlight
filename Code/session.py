import socket, time, threading, logging
import random
import string

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(threadName)s: %(message)s', datefmt='%Y.%m.%d %H:%M:%S')  # %Y.%m.%d %H:%M:%S

USED_SESSION_IDS = []

VERSION = "1.1.1"

## Role defs
HOST = 0
USER = 1
ADMIN = 2
VALID_ROLES = [HOST, USER, ADMIN]


def get_random_alphanumeric_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    result_str = ''.join((random.choice(letters_and_digits) for i in range(length)))
    return(result_str)

class enlightSession():
    ''' The main session class '''
    def __init__(self, name = "", role = HOST, password = ""):
        self.sessionName = name
        self.__activ__  = False

        ## For HOST role
        self.sessionId = None
        self.__server__ = None
        self.__server_thread__ = None
        self.sessionPassword = password
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

        if(self.sessionPassword == ""):
            self.passwordSet = "0"
        else:
            self.passwordSet = "1"

        if(self.__role__ not in VALID_ROLES):
            self.__role__ = HOST
            logging.warning("No vaild session role was set, using HOST as default")
        
        if(self.__role__ == HOST and name == ""):
            logging.warning("Role is set to HOST, but no session name was given.")
            self.sessionName = "Unnamed session"
        
    
    def initConnection(self):
        ''' Starts the main dicovery/connction method(s) '''
        global USED_SESSION_IDS
        if(self.__role__ == HOST):
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

            self.__direct_socket__ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # self.__direct_socket__.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.__direct_socket__.bind(("", 65533))
            self.__direct_thread__ = threading.Thread(target=self.lightSearcherMain, args=(), name="Inbound session server")

        elif(self.__role__ == USER or self.__role__ == ADMIN):
            self.__client__ = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # UDP
            self.__client__.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.__client__.bind(("", 37020))
            logging.info("Starting lighthouse thread")
            self.__activ__  = True
            self.__client_thread__ = threading.Thread(target=self.lighthouseMain, args=(), name="Lighthouse server")
            self.__client_thread__.start()
            
            
    def lightSearcherMain(self):
        logging.info("Inbound connection handler started")
        self.__direct_socket__.listen()
        while self.allowJoin:
            ''' The main thread for clients to connect '''
            try:
                conn, addr = self.__direct_socket__.accept()
                data, addr = self.__direct_socket__.recvfrom(1024)
            except OSError:
                logging.warning("Client socket, failure. Session maybe not avaiable anymore?")
            else:
                print(data)
        logging.info("Inbound connection handler stopped")

    def lighthouseMain(self):
        ''' The main thread for searching/finding sessions '''
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
        if(self.__role__ != HOST):
            logging.info("Clearing all know session")
            self.allOnlineSessions = {}

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

    def getSessionMembers(self):
        return(self.members)
    
    def getSessionId(self):
        return(self.sessionId)

    def join(self, sessionID):
        if(not self.connected):
            try:
                data = self.allOnlineSessions[sessionID]
            except KeyError:
                logging.error("an unknow/undiscorverd session ID was given")
                return(-2)
            else:
                try:
                    #print((data[len(data)-1][0], 65533))
                    ## Try to open a socket to the ip/port
                    self.__direct_socket__ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # UDP
                    self.__direct_socket__.connect((data[len(data)-1][0], 65533))
                    
                    self.__direct_socket__.sendall(b'CONNECT')
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
        ''' Leaves the session, can takes at least two seconds '''
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
        if(self.__role__ == HOST):
            self.allowJoin = False
            self.__activ__ = False
            # TODO: Kick all users
            self.members = []
            self.__server_thread__ = None
            self.__server__.shutdown(socket.SHUT_RDWR)
            self.__server__.close()
            self.__direct_socket__.shutdown(socket.SHUT_RDWR)
            self.__direct_socket__.close()
            logging.info("Closed Discovery server port")
        else:
            logging.warning("stopSession was called, without the role set to HOST. Did you mean .leave?")

def testModule():
    testSession = enlightSession("TestSession", role = HOST)
    userSession = enlightSession("myLocalSession", role = USER)
    userSession.initConnection()
    testSession.initConnection()
    time.sleep(5)
    userSession.join(testSession.getSessionId())
    time.sleep(5)
    testSession.stopSession()
    userSession.leave()

testModule()