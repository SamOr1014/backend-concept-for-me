import socket 
import threading
from typing import List, Tuple
from algorithm import Algo

class LoadBalancer:
    def __init__(self, port: int = 8080, host: str = "localhost", servers: List[Tuple[str, int]] = None, algorithm="round_robin"):
        self.host = host
        self.port = port
        self.servers = servers or []
        self.lb_server_socket = None
        self.algorithum_instance = Algo(self.servers)
        self.algorithm = algorithm


    def start(self):
        
        # AF_INET = IPv4, SOCK_STREAM = TCP
        self.lb_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # port to be reused immediately after restart
        self.lb_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        self.lb_server_socket.bind((self.host, self.port))
        self.lb_server_socket.listen(socket.SOMAXCONN)
        
        # Loop to listen and accept incoming connections
        while True:
            client_socket, client_address = self.lb_server_socket.accept()
            print(f"Connection from {client_address}")
            t = threading.Thread(target=self.handle_client, args=(client_socket, ))
            t.start()
            

    def handle_client(self, client_socket: socket.socket):
        try: 
            # Get all the byte from the request 
            request = b""
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                request += chunk
                if b"\r\n\r\n" in request:
                    break
                
            if not request:
                client_socket.close()
                return

            # use algo to select next be server
            
            
            match self.algorithm:
                case "round_robin":
                    backend_host, backend_port = self.algorithum_instance.round_robin()
                case "least_connections":
                    backend_host, backend_port = self.algorithum_instance.select_least_connections()
                case _:
                    backend_host, backend_port = self.algorithum_instance.round_robin()  # Default to round-robin for now
            
            #  Direct the request to the next backend server using algo
            backend_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            backend_socket.connect((backend_host, backend_port))
            self.algorithum_instance.increment_count(self.servers.index((backend_host, backend_port)))  # Increment connection count for least connections
            backend_socket.sendall(request)
            
            response = b""
            while True:
                chunk = backend_socket.recv(4096)
                if not chunk:
                    break
                response += chunk
                
            backend_socket.close()
            self.algorithum_instance.decrement_count(self.servers.index((backend_host, backend_port)))  # Decrement connection count for least connections
            
            print(f"Print load balancer received response from backend and sending back to client, res from backend {backend_host}:{backend_port}")
            # Send the response back to the client
            client_socket.sendall(response)
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            # 6. Close the client connection
            client_socket.close()
            
if __name__ == "__main__":
    # Example backend servers (host, port)
    backend_servers = [("localhost", 8081), ("localhost", 8082)]
    
    lb = LoadBalancer(port=8080, servers=backend_servers, algorithm="round_robin")
    print(f"Load balancer listening on http://{lb.host}:{lb.port}")
    lb.start()