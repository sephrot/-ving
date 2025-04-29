from socket import *
from struct import *
import struct
import time
headerFormat = '!HHHH'

def now():
	return time.ctime(time.time())

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
window = 25
nextSeqSum = 1


def startHandshake():
    global seqNum
    windowList = []
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


def finish(clientSocket, serverName, serverPort):
    flags = 0b1000
    data = createPacket(nextSeqNum, ack, flags, window, None)
    clientSocket.sendto(data, (serverName,serverPort))
        
def main():
    global nextSeqNum
    base = 0
    flags = 0
    nextSeqNum = 1
    windowlist = []
    datalist = {}
    clientSocket.settimeout(0.4)
    try:
        startHandshake()
    except Exception as e:
        print(e, " Some error happened during the handshake")
      
    with open("test.txt", "rb") as f:
        while True:
            

            '''if not packet:
                print("Connection Teardown:\n")
                finish(clientSocket,serverName, serverPort)
                print("Fin packet is sent")'''
    
            while nextSeqNum <= base + window:    
                packet = f.read(992)
                if not packet:
                    break
                data = createPacket(nextSeqNum, ack, flags, window, packet)
                windowlist.append(nextSeqNum)
                datalist[nextSeqNum] = data
                clientSocket.sendto(data, (serverName, serverPort))
                time.sleep(0.001)
                
                print(f"{now()} -- packet with seq = {nextSeqNum} is sent, sliding window = ", windowlist)
                nextSeqNum += 1
            
            try:
                message, serverAddress = clientSocket.recvfrom(2048)
                serverAck = parseHeader(message[:8])[1]
                serverFlags = parseHeader(message[:8])[2]


                if serverFlags == 0b1010:
                    print("FIN ACK packet is recieved")
                    print("Connection Closes")
                    clientSocket.close()
                    break
                elif serverAck > base:
                    print("ServerAck: ", serverAck, " Base: ", base)
                    print(f"ACK {serverAck} received correctly")
                    base = serverAck
                    if (serverAck) in windowlist:
                        
                        windowlist.remove(serverAck)
                        if len(windowlist) == 0:
                            print("Connection Teardown:\n")
                            finish(clientSocket,serverName, serverPort)
                            print("Fin packet is sent")
                elif serverAck != base:
                    print(f"ACK mismatch: expected {base} but got {serverAck}")
                
            except socket.timeout:
                print("Timeout occurred! Need to retransmit packet.")
                for seq in windowlist:
                    clientSocket.sendto(datalist[seq],(serverName, serverPort))
                

if __name__ == "__main__":
    main()


