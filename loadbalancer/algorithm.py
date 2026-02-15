class Algo():
    def __init__(self, servers):
        self.servers = servers
        self.current = 0
        self.connection_counts = [0] * len(self.servers)  # For least connections
        self.weights = [1] * len(self.servers)            # For weighted algorithms
        self.response_times = [0.1] * len(self.servers)   # For response time
        self.health = [True] * len(self.servers)          # For health checks
        
    def round_robin(self):
        server = self.servers[self.current]
        self.current = (self.current + 1) % len(self.servers)
        return server

    def select_least_connections(self):
        # Find the server with the fewest active connections
        min_conn = min(self.connection_counts)
        idx = self.connection_counts.index(min_conn)
        return self.servers[idx], idx

    def increment_count(self, idx):
        self.connection_counts[idx] += 1

    def decrement_count(self, idx):
        self.connection_counts[idx] -= 1