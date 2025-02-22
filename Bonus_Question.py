import socket
import threading
import select
import sys

class Peer:
    def __init__(self, name, port):
        self.name = name
        self.port = int(port)
        self.peers = {}  # Store connected peers as {ip: {port: socket}}
        self.server_socket = None

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('', self.port))
        self.server_socket.listen(5)

        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"Connection from {addr}")
            self.handle_client(client_socket, addr)

    def handle_client(self, client_socket, addr):
        while True:
            try:
                message = client_socket.recv(1024).decode()
                if message:
                    if message.startswith("CONNECT"):  # Handle connection message
                        _, peer_ip, peer_port = message.split()
                        peer_port = int(peer_port)
                        if peer_ip not in self.peers:
                            self.peers[peer_ip] = {}
                        self.peers[peer_ip][peer_port] = client_socket # Add to connected peers
                        print(f"Peer {addr} connected to {peer_ip}:{peer_port}")
                    elif message == "EXIT":
                        self.remove_peer(addr)
                        client_socket.close()
                        break
                    else:
                        print(f"Received from {addr}: {message}")
                else:
                    self.remove_peer(addr)
                    client_socket.close()
                    break
            except Exception as e:
                print(f"Error handling client {addr}: {e}")
                self.remove_peer(addr)
                client_socket.close()
                break

    def remove_peer(self, addr):
        ip, port = addr
        if ip in self.peers and port in self.peers[ip]:
            del self.peers[ip][port]
            print(f"Peer {addr} disconnected.")
            if not self.peers[ip]: # Remove IP if no ports are associated with it
                del self.peers[ip]


    def send_message(self, ip, port, message):
        try:
            if ip in self.peers and port in self.peers[ip]:
                sock = self.peers[ip][port]
                sock.send(message.encode())
            else:
                print(f"Peer {ip}:{port} is not connected.")
        except Exception as e:
            print(f"Error sending message: {e}")

    def query_peers(self):
        if self.peers:
            print("Active Peers:")
            for ip, ports in self.peers.items():
                for port in ports:
                    print(f"{ip}:{port}")
        else:
            print("No active peers.")

    def connect_to_peer(self, ip, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, int(port)))
            if ip not in self.peers:
                self.peers[ip] = {}
            self.peers[ip][int(port)] = sock
            sock.send(f"CONNECT {ip} {self.port}".encode()) # Send connection message
            print(f"Connected to {ip}:{port}")
            return sock
        except Exception as e:
            print(f"Error connecting to {ip}:{port}: {e}")
            return None

    def run(self):
        print(f"Server listening on port {self.port}")
        server_thread = threading.Thread(target=self.start_server)
        server_thread.daemon = True
        server_thread.start()

        while True:
            print("\n***** Menu *****")
            print("1. Send message")
            print("2. Query active peers")
            print("3. Connect to active peers")
            print("0. Quit")

            choice = input("Enter your choice: ")

            if choice == '1':
                ip = input("Enter recipient IP: ")
                port = int(input("Enter recipient port: "))
                message = input("Enter your message: ")
                self.send_message(ip, port, message)
            elif choice == '2':
                self.query_peers()
            elif choice == '3':
                ip = input("Enter IP to connect: ")
                port = int(input("Enter port to connect: "))
                self.connect_to_peer(ip, port)
            elif choice == '0':
                break
            else:
                print("Invalid choice.")

if __name__ == "__main__":
    name = input("Enter your name: ")
    port = input("Enter your port number: ")
    peer = Peer(name, port)
    peer.run()