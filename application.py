from socket import *
from struct import *
import struct

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

def sendSyn(clientSocket, serverName, serverPort):
    seq = 0
    ack = 0
    flags = 0b0100
    win = 5
    data = createPacket(seq,ack,flags,win,None)
    clientSocket.sendto(data, (serverName, serverPort))

def sendAck(clientSocket, serverAddress):
    seq = 1
    ack = 1
    flags = 0b0010
    win = 5
    data = createPacket(seq,ack,flags,win,None)
    clientSocket.sendto(data, (serverAddress))


serverName = "127.0.0.1"
serverPort = 12000
clientSocket = socket(AF_INET, SOCK_DGRAM)
print("Connection Establishment Phase: \n")
seqNum = 0
ack = 1
flags = 0
window = 5



def startHandshake():
    global seqNum
    windowList = [None] * window
    while True:
        sendSyn(clientSocket, serverName, serverPort)
        clientSocket.settimeout(0.4)  # 400 milliseconds

        try:
            clientSocket.settimeout(0.4)  # 400 milliseconds
            message, serverAddress = clientSocket.recvfrom(2048) #recieves info from the server
            serverHeader = parseHeader(message[:8])
            serverMessage = message[8:].decode() #decoding the actual message.
            #This part focuses on dividing the header into subparts
            serverSeqNum = serverHeader[0] #this is the sequence number for the SERVER
            serverAckNum = serverHeader[1] #this is the servers guess about what the next CLIENT sequence number is
            serverFlags = serverHeader[2] #this tells us whether SYN, ACK, FIN

            #Here we're going to check if the flag is a SYN
            if serverFlags == 6: #STAGE 3
                print("SYN-ACK packet is recieved") #if the IF hits, it means the server got our packet and we got a SYN-ACK back.
                sendAck(clientSocket, serverAddress)
                seqNum+=1
                print("ACK packet is sent")
                print("Connection Established")
                break  
        except timeout:
            print("Timeout occurred! Need to retransmit or handle it.")



        
def main():
    global seqNum
    data = ""
    try:
        startHandshake()
    except Exception as e:
        print(e, " Some error happened during the handshake")
      
    with open("test.txt", "rb") as f:
        while True:
            packet = f.read(992)
            if not packet:
                print("End of file reached")
                break
                
            data = createPacket(seqNum, ack, flags, window, packet)
            
            try:
                clientSocket.sendto(data, (serverName, serverPort))
                clientSocket.settimeout(0.4)
                
                message, serverAddress = clientSocket.recvfrom(2048)
                serverAck = parseHeader(message[:8])[1]
                
                if serverAck == seqNum + 1:
                    print(f"ACK {serverAck} received correctly")
                    seqNum += 1
                else:
                    print(f"ACK mismatch: expected {seqNum} but got {serverAck}")
                    
            except timeout:
                print("Timeout occurred! Need to retransmit packet.")
                # You would need to resend the same packet


if __name__ == "__main__":
    main()

clientSocket.close()

