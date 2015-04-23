#!/usr/bin/python

"""
Spear Client Bot that queries for random Alphanumeric Code
at random intervals
"""

import socket
import random
import time
import sys
import spear.databaseConstants as const

letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
numbers = '0123456789'

def _getRandomCode():

    letterCode = []
    numberCode = []

    letterCode.append(letters[random.randint(0, 25)])
    letterCode.append(letters[random.randint(0, 25)])
    letterCode.append(letters[random.randint(0, 25)])

    numberCode.append(numbers[random.randint(0, 9)])
    numberCode.append(numbers[random.randint(0, 9)])
    numberCode.append(numbers[random.randint(0, 9)])

    letterStr = ''.join(letterCode)
    numberStr = ''.join(numberCode)

    plateCode = letterStr + numberStr

    return plateCode

random.seed()

#Parse argument in form IP:PORT
IP = sys.argv[1]
port = int(sys.argv[2])

serverIP = IP
serverPort = int(port)

totalTime = 0
numberQuery = 0

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

clientSocket.connect((serverIP, serverPort))

print "SPEAR Client Bot connected to %s:%s" %(serverIP, serverPort)

while True:

    toSend = _getRandomCode()

    print "Sent: %s" %toSend

    clientSocket.send(toSend)

    try:
        timeSent = time.time()
        received = clientSocket.recv(2048).strip("\n")
        timeReceived = time.time()

        processTime = timeReceived - timeSent

        totalTime += processTime
        numberQuery += 1

        aveTime = float(totalTime) / float(numberQuery)

        print '/'.join(const.interpretCode(int(received)))
        print "Received in [%f s]. Average Time: [%f s]" %(processTime, aveTime)
        print ""

    except:
        break

    #Random Delay [4 - 6 seconds]
    random_interval = random.random() * 2
    time.sleep(4 + random_interval)

print "Closing Server connection..."
clientSocket.close()


