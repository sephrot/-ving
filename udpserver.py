from socket import *
from struct import *
import struct
import time 

seq = 0 #meant to keep track of what the server is sendign
ack = 0 #meant to keep track of whats expected from client
flags = 0b0010 # 1000 is fin flag, 0100 is syn, 0010 is A, 0001 is R
window = 0
windowList = []

serverPort = 12000
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', serverPort))

headerFormat = '!HHHH'


def createPacket(seq, ack, flags, win, data):
    header = pack(headerFormat, seq, ack, flags, win)
    if data is None:
        packet = header
    else:
        packet = header + data 
    return packet


def parseFlags(flags):
    syn = flags & (1 << 3)
    ack = flags & (1 << 2)
    fin = flags & (1 << 1)
    return syn, ack, fin

def parseHeader(header):
    headerFromMsg = unpack(headerFormat, header)
    return headerFromMsg


def sendAck(serverSocket, clientAddress):
    global ack
    global seq
    flags = 0b0010
    win = 5
    data = createPacket(seq,ack,flags,win,None)
    serverSocket.sendto(data, (clientAddress))

def sendSynAck(serverSocket, clientAddress):
    seq = 0
    ack = 1
    flags = 0b0110
    win = 5
    data = createPacket(seq,ack,flags,win,None)
    serverSocket.sendto(data, (clientAddress))

def now():
	return time.ctime(time.time())

while True:
    try:
        message, clientAddress = serverSocket.recvfrom(1000)
        clientHeader = parseHeader(message[:8])
        
        clientSeqNum = clientHeader[0]
        cAckNum = clientHeader[1] #the clients expected ack num from the server
        cFlags = clientHeader[2]

        data = message[8:].decode()

        if cFlags == 4:
            ack += 1
            print("SYN packet is recieved")
            sendSynAck(serverSocket, clientAddress)
            print("Amount of times client has sent to me: ", clientSeqNum)    
            print("SYN-ACK packet is sent")
            seq+=1

        elif cFlags == 2:
            print("Server: Connection established")
            print("Ready to recieve data")
            flags = 0
            break
    except Exception as e:
        print("Something went wrong.")


while True:
    try:
        message, clientAddress = serverSocket.recvfrom(1000)
        clientHeader = parseHeader(message[:8])
        
        clientSeqNum = clientHeader[0]
        cAckNum = clientHeader[1] #the clients expected ack num from the server
        cFlags = clientHeader[2]

        if ack == clientSeqNum:
            print("Expected: ", ack, " Actual: ", clientSeqNum, "\n")
            print(message[8:].decode())
            ack += 1
            sendAck(serverSocket, clientAddress)
        else:
            sendAck(serverSocket, clientAddress)
    except ConnectionResetError:
         print("No more data left!")
         break
          
    
     
       



         
