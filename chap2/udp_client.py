import socket

target_host = "127.0.0.1"
target_port = 9997

# Create a socket object
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # AF_INET indique lutilisation ipv4 ou nom d'hote standart, SOCK_DGRAM indique que c'est un client udp

# Send some data
client.sendto(b"AAABBBCCC",(target_host, target_port)) # b"AAABBBCCC" est un byte string

# Receive some data
data, addr = client.recvfrom(4096) # 4096 est la taille du buffer

print(data.decode())
client.close()

