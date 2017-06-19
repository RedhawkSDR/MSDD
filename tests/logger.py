import os, sys, time
import socket

if __name__ == "__main__":

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("", 8900))
    while 1:
        data, addr = s.recvfrom(1024)
        print data
