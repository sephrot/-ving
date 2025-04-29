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
def serverHandshake():
    global seq, ack
    while True:
        try:
            message, clientAddress = serverSocket.recvfrom(1000)
            clientHeader = parseHeader(message[:8])
            
            clientSeqNum = clientHeader[0]
            cAckNum = clientHeader[1] #the clients expected ack num from the server
            cFlags = clientHeader[2]

            data = message[8:]

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
                break
        except Exception as e:
            print("Something went wrong.", e)

def main():
    global ack, seq
    print(ack)
    serverHandshake()
    print(ack)
    flags = 0
    received_packets = {}
    while True:
        
        try:
            message, clientAddress = serverSocket.recvfrom(1000)
            clientHeader = parseHeader(message[:8])
            
            clientSeqNum = clientHeader[0]
            clientFlag = clientHeader[2]
            data = message[8:]     
            
            if ack == clientSeqNum:
                print("Expected: ", ack, " Actual: ", clientSeqNum, "\n")
                received_packets[clientSeqNum] = data
                sendAck(serverSocket, clientAddress)
                ack += 1
            else:
                sendAck(serverSocket, clientAddress)
                if clientSeqNum not in received_packets:
                    received_packets[clientSeqNum] = data
                    

            if clientFlag == 0b1000:
                print("FIN packet is recieved")
                flags = 0b1010
                data = createPacket(seq, ack, flags, 5, None)
                serverSocket.sendto(data, clientAddress)
                print("Fin ACK packet is sent.")
                print("Connection Closes")


                break
        except ConnectionResetError:
            print("No more data left!")
            break
          
    
    with open("1.jpg", "wb") as f:
        for i in sorted(received_packets.keys()):
            f.write(received_packets[i])
            
if __name__ == "__main__":
    main()


         
