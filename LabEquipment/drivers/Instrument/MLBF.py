import socket

class MLBF(object):
    """Class for operating the Micro Lambda Wireless MLBF series of
    benchtop YIG filters, using UDP sockets over ethernet"""
    def __init__(self, ip_address, port=30303):
        self.ip_address = ip_address
        self.port = port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.ip_address, self.port)

    def read(self, bytesize=1024):
        """Listen for <bytesize> bytes from UDP client"""
        while True:
            data, addr = self.sock.recvfrom(bytesize)
            print "Message: ", data

            if data:
                break

        return data

    def write(self, message):
        """Write message to UDP client"""
        self.sock.sendto(message, (self.ip_address, self.port))
