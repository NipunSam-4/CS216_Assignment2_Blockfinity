import socket
import threading
import sys

class Peer:
    def __init__(self, name, port, known_peers):
        self.name = name
        self.port = int(port)
        self.known_peers = known_peers  # List of (IP, port) tuples
        self.received_from = {}  # Track messages received from peers {ip: {port: name}}
        self.server_socket = None

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('', self.port))
        self.server_socket.listen(5)
        print(f"Server listening on port {self.port}")

        while True:
            client_socket, addr = self.server_socket.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
            client_thread.start()

    def handle_client(self, client_socket, addr):
        while True:
            try:
                message = client_socket.recv(1024).decode()
                if message:
                    try:
                        peer_address, peer_name, actual_message = message.split(" ", 2)
                        ip, port = peer_address.split(":")
                        port = int(port)

                        if actual_message.lower() == "exit":
                            self.remove_peer(ip, port)
                            print(f"Peer {peer_address} ({peer_name}) disconnected.")
                            break
                        
                        if ip not in self.received_from:
                            self.received_from[ip] = {}
                        if port not in self.received_from[ip]:
                            self.received_from[ip][port] = peer_name

                        print(f"{peer_address} {peer_name} {actual_message}")
                    except ValueError:
                        print(f"Invalid message format from {addr}: {message}")
                else:
                    break  # Client disconnected
            except Exception as e:
                print(f"Error handling client {addr}: {e}")
                break
        client_socket.close()

    def send_message(self, recipient_ip, recipient_port, message):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((recipient_ip, recipient_port))
            formatted_message = f"{socket.gethostbyname(socket.gethostname())}:{self.port} {self.name} {message}"
            sock.send(formatted_message.encode())
            sock.close()
            print(f"Message sent to {recipient_ip}:{recipient_port}")

            if message.lower() == "exit":
                self.remove_peer(recipient_ip, recipient_port)
                print(f"Disconnected from {recipient_ip}:{recipient_port}")
        except Exception as e:
            print(f"Error sending message to {recipient_ip}:{recipient_port}: {e}")

    def remove_peer(self, ip, port):
        if ip in self.received_from and port in self.received_from[ip]:
            del self.received_from[ip][port]
            if not self.received_from[ip]:  # Remove IP if no ports remain
                del self.received_from[ip]

    def query_received_from(self):
        if self.received_from:
            print("Connected Peers:")
            for ip, ports in self.received_from.items():
                for port, name in ports.items():
                    print(f"({name}){ip}:{port}")
        else:
            print("No active peers.")

    def run(self):
        server_thread = threading.Thread(target=self.start_server)
        server_thread.daemon = True  # Allow main thread to exit
        server_thread.start()

        for ip, port in self.known_peers:  # Send initial messages to known peers
            self.send_message(ip, port, "Hello from " + self.name)  # Say hello to known peers

        while True:
            print("\n***** Menu *****")
            print("1. Send message")
            print("2. Query received from")
            print("0. Quit\n")

            choice = input("Enter your choice: \n")

            if choice == '1':
                ip = input("Enter recipient IP: ")
                port = int(input("Enter recipient port: "))
                message = input("Enter your message: ")
                self.send_message(ip, port, message)
            elif choice == '2':
                self.query_received_from()
            elif choice == '0':
                break
            else:
                print("Invalid choice.")

if __name__ == "__main__":
    name = input("Enter your name: ")
    port = input("Enter your port number: ")
    known_peers = [("10.206.4.122", 1255), ("10.206.5.228", 6555)]  # Mandatory peers
    peer = Peer(name, port, known_peers)
    peer.run()
