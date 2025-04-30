from socket import *
from struct import *
import socket
import struct
import time
import sys, argparse


clientAck = 1
clientFlags = 0

serverAAck = 0

nextSeqNum = 1

headerFormat = '!HHHH'


parser = argparse.ArgumentParser(description="Optional arguments: checking IPv4 address", epilog="end of help") #sets up an arguments parser that can handle command-line inputs via variable "parser"
parser.add_argument('-i' , '--ip', type=str, required=True) #uses parser variable to add three arguments. Gives the argument type and if the required argument is true
parser.add_argument('-p' , '--port', type=int, required=True)
parser.add_argument('-f' , '--file', type=str, required=False)
parser.add_argument('-w' , '--window', type=str, required=False)
parser.add_argument('-d', '--discard', type=int, required = False,
                    help='Sequence number to discard once for retransmission testing')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-s', '--server', action='store_true', help='Run as server')
group.add_argument('-c', '--client', action='store_true', help='Run as client')


args = parser.parse_args() #parses the command-line arguments created

clientSocket = socket.socket(AF_INET, SOCK_DGRAM)
serverSocket = socket.socket(AF_INET, SOCK_DGRAM)

serverName = args.ip
serverPort = args.port
filepath = args.file
runServer = args.server
runClient = args.client
windowSize = int(args.window)

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

def sendAck(clientSocket, serverAddress,seq,ack):
    flags = 0b0010
    win = 5
    data = createPacket(seq,ack,flags,win,None)
    clientSocket.sendto(data, (serverAddress))

def sendSynAck(serverSocket, clientAddress):
    seq = 0
    ack = 1
    flags = 0b0110
    win = 5
    data = createPacket(seq,ack,flags,win,None)
    serverSocket.sendto(data, (clientAddress))


def finish(clientSocket, serverName, serverPort):
    global nextSeqNum, clientAck
    flags = 0b1000
    data = createPacket(nextSeqNum, clientAck, flags, windowSize, None)
    clientSocket.sendto(data, (serverName,serverPort))

def clientHandshake():
    while True:
        sendSyn(clientSocket, serverName, serverPort)
        print("SYN packet is sent")
        clientSocket.settimeout(0.4)  # 400 milliseconds

        try:
            clientSocket.settimeout(0.4)  # 400 milliseconds
            message, serverAddress = clientSocket.recvfrom(2048) #recieves info from the server
            serverHeader = parseHeader(message[:8])
            
            serverFlags = serverHeader[2] #this tells us whether SYN, ACK, FIN

            #Here we're going to check if the flag is a SYN
            if serverFlags == 6: #STAGE 3
                print("SYN-ACK packet is recieved") #if the IF hits, it means the server got our packet and we got a SYN-ACK back.
                sendAck(clientSocket, serverAddress,1,clientAck)
                print("ACK packet is sent")
                print("Connection Established\n")
                break  
        except timeout:
            print("Timeout occurred! Need to retransmit or handle it.")



def clientSending():
    print("Connection Establishment Phase: \n")
    global nextSeqNum
    base = 0
    clientFlags = 0
    nextSeqNum = 1
    clientAck = 1
    windowlist = []
    datalist = {}
    clientSocket.settimeout(0.4)
    try:
        clientHandshake()
    except Exception as e:
        print(e, " Some error happened during the handshake")
      
    with open(filepath, "rb") as f:
        while True:
            while nextSeqNum <= base + windowSize:    
                packet = f.read(992)
                if not packet:
                    break
                data = createPacket(nextSeqNum, clientAck, clientFlags, windowSize, packet)
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
                    print(f"Sliding window moved: base updated to {base}")
                    base = serverAck
                    #print(f"{now()} -- ACK for packet is {serverAck} received")
                    if (serverAck) in windowlist:
                        windowlist.remove(serverAck)
                        if len(windowlist) == 0:
                            print("......\n")
                            print("DATA Finished\n\n")
                            print("Connection Teardown:\n")
                            finish(clientSocket,serverName, serverPort)
                            print("Fin packet is sent")
                    
                elif serverAck != base:
                    print(f"ACK mismatch: expected {base} but got {serverAck}")
                
            except socket.timeout:
                print("Timeout occurred! Need to retransmit packet.")
                for seq in range(base, nextSeqNum):
                    clientSocket.sendto(datalist[seq],(serverName, serverPort))

    
def serverHandshake():
    serverSocket.bind((serverName, serverPort))
    global serverAAck
    while True:
        try:
            message, clientAddress = serverSocket.recvfrom(1000)
            clientHeader = parseHeader(message[:8])
            
            clientSeqNum = clientHeader[0]
            cAckNum = clientHeader[1] #the clients expected ack num from the server
            cFlags = clientHeader[2]

            data = message[8:]

            if cFlags == 4:
                serverAAck += 1
                print("SYN packet is recieved")
                sendSynAck(serverSocket, clientAddress)
                print("Amount of times client has sent to me: ", clientSeqNum)    
                print("SYN-ACK packet is sent")

            elif cFlags == 2:
                print("Server: Connection established")
                print("Ready to recieve data")
                break
        except Exception as e:
            print("Something went wrong.", e)

def serverSide():
    global serverAAck, seq
    discard_seq = args.discard
    discarded = False

    serverHandshake()

    flags = 0
    received_packets = {}
    start_time = None
    end_time = None
    while True:


        
        try:
            message, clientAddress = serverSocket.recvfrom(1000)
            clientHeader = parseHeader(message[:8])
            
            clientSeqNum = clientHeader[0]
            clientFlag = clientHeader[2]
            data = message[8:]     

            if start_time is None and clientFlag != 0b1000:
                start_time = time.time()
            print(clientSeqNum, " ", discard_seq)
            if clientSeqNum == discard_seq and not discarded:
                print(f"[TEST] Discarding packet with seq = {clientSeqNum} once to test retransmission")
                discarded = True
                continue  # Simulate loss by not ACKing or storing the packet

            if serverAAck == clientSeqNum:
                print("Expected: ", serverAAck, " Actual: ", clientSeqNum, "\n")
                received_packets[clientSeqNum] = data
                sendAck(serverSocket, clientAddress, 1, serverAAck)
                serverAAck += 1
            else:
                print(f"Out-of-order packet {clientSeqNum} received. Expected {serverAAck}. Discarding.")
                
                    

            if clientFlag == 0b1000:
                end_time = time.time()
                print("FIN packet is recieved")
                flags = 0b1010
                data = createPacket(1, serverAAck, flags, 5, None)
                serverSocket.sendto(data, clientAddress)
                print("Fin ACK packet is sent.")
                print("Connection Closes")


                break
        except ConnectionResetError:
            print("No more data left!")
            break

    duration = end_time - start_time
    total_bytes = sum(len(received_packets[i]) for i in received_packets)
    throughput_mbps = (total_bytes * 8) / (duration * 1_000_000)

    print(f"Throughput: {throughput_mbps:.3f} Mbps")
     
    with open("1.jpg", "wb") as f:
        for i in sorted(received_packets.keys()):
            f.write(received_packets[i])


def main():
    if runClient:
        print("Starting server...")      
        clientSending()
    if runServer:
        print("Staring server...")
        serverSide()

if __name__ == "__main__":
    main()

