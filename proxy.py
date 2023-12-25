import sys  # lib pour les fonctions système
import socket  # lib pour les fonctions réseau
import threading  # lib pour les threads

HEX_FILTER = ''.join([(len(repr(chr(i))) == 3) and chr(i) or '.' for i in range(256)])  # filtre pour les caractères non affichables

def hexdump(src, length=16, show=True):  # fonction pour afficher les données en hexadécimal
    if isinstance(src, bytes):  # si les données sont des bytes
        src = src.decode()
    results = list()  # liste pour stocker les données
    for i in range(0, len(src), length):  # pour chaque octet
        word = str(src[i:i+length])  # récupérer les données
        printable = word.translate(HEX_FILTER)  # filtrer les caractères non affichables
        hexa = ' '.join([f'{ord(c):02X}' for c in word])  # convertir les données en hexadécimal
        hexwidth = length * 3  # calculer la largeur de l'affichage hexadécimal
        results.append(f'{i:04x} {hexa:<{hexwidth}} {printable}')  # ajouter les données à la liste
    if show:
        for line in results:
            print(line)
    else:
        return results

# Fonction pour recevoir des données
def receive_from(connection):
    buffer = b''
    connection.settimeout(5)
    try:
        while True:
            data = connection.recv(4096)
            if not data:
                break
            buffer += data
    except TimeoutError:
        pass
    return buffer

# Fonction pour gérer les requêtes
def request_handler(buffer):
    # effectuer des modifications sur les paquets
    return buffer

# Fonction pour gérer les réponses
def response_handler(buffer):
    # effectuer des modifications sur les paquets
    return buffer

# Fonction pour gérer le proxy
def proxy_handler(client_socket, remote_host, remote_port, receive_first):
    # se connecter au serveur distant
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_socket.connect((remote_host, remote_port))
    # recevoir des données du serveur distant si nécessaire
    if receive_first:
        remote_buffer = receive_from(remote_socket)
        hexdump(remote_buffer)
        # envoyer les données au gestionnaire de réponse
        remote_buffer = response_handler(remote_buffer)
        # si des données sont disponibles, les envoyer au client local
        if len(remote_buffer):
            print('[<==] Envoi de %d octets au localhost.' % len(remote_buffer))
            client_socket.send(remote_buffer)
    # boucler et lire du local, envoyer au distant, envoyer au local
    while True:
        # lire du local
        local_buffer = receive_from(client_socket)
        if len(local_buffer):
            print('[==>] Réception de %d octets du localhost.' % len(local_buffer))
            hexdump(local_buffer)
            # envoyer les données au gestionnaire de requête
            local_buffer = request_handler(local_buffer)
            # envoyer les données au serveur distant
            remote_socket.send(local_buffer)
            print('[==>] Envoi de %d octets au distant.' % len(local_buffer))
        # recevoir la réponse
        remote_buffer = receive_from(remote_socket)
        if len(remote_buffer):
            print('[<==] Réception de %d octets du distant.' % len(remote_buffer))
            hexdump(remote_buffer)
            # envoyer les données au gestionnaire de réponse
            remote_buffer = response_handler(remote_buffer)
            # envoyer la réponse au socket local
            client_socket.send(remote_buffer)
            print('[<==] Envoi de %d octets au localhost.' % len(remote_buffer))
        # si plus de données des deux côtés, fermer les connexions
        if not len(local_buffer) or not len(remote_buffer):
            client_socket.close()
            remote_socket.close()
            print('[*] Plus de données. Fermeture des connexions.')
            break

def server_loop(local_host, local_port, remote_host, remote_port, receive_first):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # création du socket
    try:
        server.bind((local_host, local_port))  # liaison du socket au port et à l'adresse
    except OSError:
        print('[!!] Échec de l\'écoute sur %s:%d' % (local_host, local_port))
        print('[!!] Vérifiez les autorisations de liaison et les paramètres de pare-feu.')
        sys.exit(0) # arrêt du programme
    print('[*] Écoute sur %s:%d' % (local_host, local_port))
    server.listen(5)  # écoute du socket
    while True:
        client_socket, addr = server.accept()  # accepter les connexions entrantes
        # afficher les informations sur la connexion entrante
        print('[==>] Réception de la connexion entrante de %s:%d' % (addr[0], addr[1]))
        # démarrer un thread pour gérer la connexion entrante
        proxy_thread = threading.Thread(
            target=proxy_handler, 
            args=(client_socket, remote_host, remote_port, receive_first))
        proxy_thread.start()
        
def main():
    # pas de mise en mémoire tampon lors de l'envoi/réception
    socket.setdefaulttimeout(5)
    
    # Analyse des arguments de la ligne de commande
    if len(sys.argv[1:]) != 5:
        print("Usage: ./proxy.py [localhost] [localport]", end='')
        print("[remotehost] [remoteport] [receive_first]")
        print("Example: ./proxy.py 127.0.0.1 9000 10.12.132.1 9000 True")
        sys.exit(0)
    
    # Récupération des paramètres de la ligne de commande
    local_host = sys.argv[1]
    local_port = int(sys.argv[2])
    remote_host = sys.argv[3]
    remote_port = int(sys.argv[4])
    
    # Indique si les données doivent être reçues en premier
    receive_first = sys.argv[5]
    
    if "True" in receive_first:
        receive_first = True
    else:
        receive_first = False
    
    # Appel de la boucle du serveur proxy
    server_loop(local_host, local_port, remote_host, remote_port, receive_first)

# La fonction __name__ est '__main__' seulement si le script est exécuté directement
if __name__ == '__main__':
    main()
