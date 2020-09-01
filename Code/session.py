import socket, time, asyncio, threading
import random
import string

def get_random_alphanumeric_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    result_str = ''.join((random.choice(letters_and_digits) for i in range(length)))
    print("Random alphanumeric String is:", result_str)
## get_random_alphanumeric_string(24)

uniqueString = "tTk8ppDJaqnHWP3z8cNCiXVY"

sessionName = "TestSession"
sessionPassword = ""
Members = []

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # UDP
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

# Enable port reusage so we will be able to run multiple clients and servers on single (host, port).
# Do not use socket.SO_REUSEADDR except you using linux(kernel<3.9): goto https://stackoverflow.com/questions/14388706/how-do-so-reuseaddr-and-so-reuseport-differ for more information.
# For linux hosts all sockets that want to share the same address and port combination must belong to processes that share the same effective user ID!
# So, on linux(kernel>=3.9) you have to run multiple servers and clients under one user to share the same (host, port).
# Thanks to @stevenreddie
#   client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

# Enable broadcasting mode
client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

client.bind(("", 37020))



def serverMain():
    print("Server main started")
    # Set a timeout so the socket does not block
    # indefinitely when trying to receive data.
    server.settimeout(0.2)
    message = b"SESSION;" + sessionName.encode("utf-8") + b";" + uniqueString.encode("utf-8") + b"|"
    i = 0
    while i<=10:
        server.sendto(message, ("<broadcast>", 37020))
        print(f"Sent at {time.strftime('%X')}")
        print("message sent!")
        time.sleep(1)
        i+=1
    print("Server quited")

def clientMain():
    print("Client started")
    while True:
    # Thanks @seym45 for a fix
        data, addr = client.recvfrom(1024)
        data = data.decode("utf-8")
        data = data.replace("|", "")
        
        proc = data.split(";")
        # print(proc[2])
        if(proc[2] == uniqueString):
            print("From same device")
        print("received message: %s" % data)
        print(f"Rec at {time.strftime('%X')}")
    print("Client quited")

def main():
    #task1 = asyncio.create_task(serverMain())
    #task2 = asyncio.create_task(clientMain())
    thread = []
    thread.append(threading.Thread(target=clientMain, args=()))
    thread.append(threading.Thread(target=serverMain, args=()))
    for th in thread:
        th.start()
    
    

    #await task1
    #await task2

#asyncio.run(main())
main()
print("Quited")