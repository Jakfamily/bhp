import socket
import threading

# Définition de l'adresse IP et du port sur lesquels le serveur écoutera
IP = "0.0.0.0"  # 0.0.0.0 signifie que le serveur écoutera sur toutes les interfaces réseau disponibles
PORT = 9998


def main():
    # Création d'une socket serveur
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # AF_INET pour IPv4, SOCK_STREAM pour le protocole TCP
    server.bind((IP, PORT))  # Liaison de la socket à l'adresse et au port spécifiés
    server.listen(5)  # Le serveur peut gérer jusqu'à 5 connexions en attente
    print(f"[*] Listening on {IP}:{PORT}")

    # Boucle principale pour accepter les connexions entrantes
    while True:
        client, address = server.accept()  # Accepte la connexion du client
        print(f"[*] Accepted connection from {address[0]}:{address[1]}")

        # Création d'un thread pour gérer le client
        client_handler = threading.Thread(target=handle_client, args=(client,))
        client_handler.start()

# Fonction pour gérer un client
def handle_client(client_socket):
    with client_socket as sock:
        request = sock.recv(1024)  # Réception des données du client (1024 octets maximum)
        print(f"[*] Received: {request.decode('utf-8')}")
        sock.send(b"ACK")  # Envoi d'une réponse au client (dans ce cas, un accusé de réception)

# Point d'entrée du programme
if __name__ == "__main__":
    main()
