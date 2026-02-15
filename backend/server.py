import socket
import threading
import sys
from datetime import datetime


class HttpServer:
    """A small, educational HTTP server built on raw sockets.

    Features:
    - Accepts TCP connections
    - Parses simple HTTP requests (request-line + headers)
    - Responds to three simple routes: '/', '/health', '/api/data'
    - Uses a thread per connection (simple concurrency model)
    """

    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.server_socket = None

    def start(self):
        """Start the server, listen for connections and dispatch handlers."""
        # create a TCP socket (IPv4 + TCP)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Allow reusing the address and port immediately after restart
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind the socket to our host and port
        self.server_socket.bind((self.host, self.port))

        # Start listening; use SOMAXCONN to ask the OS for the default maximum backlog
        self.server_socket.listen(socket.SOMAXCONN)

        print(f"✓ Server listening on http://{self.host}:{self.port}")
        print("Waiting for connections... (Press Ctrl+C to stop)")

        try:
            while True:
                # This blocks until a client connects
                client_socket, client_address = self.server_socket.accept()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Connection from {client_address}")

                # Dispatch handling to a new thread so accept() stays responsive
                t = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address),
                    daemon=True,
                )
                t.start()

        except KeyboardInterrupt:
            print("\nShutting down...")
            self.server_socket.close()

    def handle_client(self, client_socket: socket.socket, client_address):
        """Read a full HTTP request from client_socket and write a response.

        This implementation is intentionally simple and synchronous per connection.
        It reads until the end of headers (CRLF CRLF) and ignores request bodies.
        """
        try:
            # Read request bytes until we have the header terminator
            client_socket.settimeout(2.0)
            request_data = b""
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                request_data += chunk
                if b"\r\n\r\n" in request_data:
                    break

            if not request_data:
                return

            # Decode request (ignore decode errors)
            try:
                request_text = request_data.decode("utf-8", errors="replace")
            except Exception:
                request_text = str(request_data)

            # Parse request-line
            request_line = request_text.splitlines()[0]
            parts = request_line.split()
            method = parts[0] if len(parts) > 0 else "GET"
            path = parts[1] if len(parts) > 1 else "/"

            print(f"Request: {method} {path} from {client_address}")

            # Simple routing
            if path == "/":
                status = "200 OK"
                content_type = "text/html; charset=utf-8"
                body = f"<html><body><h1>Backend Server</h1><p>Port: {self.port}</p></body></html>"

            elif path == "/health":
                status = "200 OK"
                content_type = "application/json"
                body = '{"status": "healthy"}'

            elif path == "/api/data":
                status = "200 OK"
                content_type = "application/json"
                body = '{"message": "Hello from backend", "port": %d}' % self.port

            else:
                status = "404 Not Found"
                content_type = "text/html; charset=utf-8"
                body = f"<html><body><h1>404 Not Found</h1><p>{path}</p></body></html>"

            # Build response
            body_bytes = body.encode("utf-8")
            response_lines = [f"HTTP/1.1 {status}", f"Content-Type: {content_type}", f"Content-Length: {len(body_bytes)}", "Connection: close", "", ""]
            response = "\r\n".join(response_lines).encode("utf-8") + body_bytes

            client_socket.sendall(response)

        except socket.timeout:
            print(f"Timeout while reading from {client_address}")
        except Exception as e:
            print(f"Error handling client {client_address}: {e}")
        finally:
            try:
                client_socket.close()
            except Exception:
                pass

if __name__ == "__main__":
    # Allow optional port via command line
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    server = HttpServer(port=port)
    print(f"Starting HTTP server on {server.host}:{server.port}")
    server.start()