import socket
import sys

def test_network_connection():
    host = '10.124.7.18'
    port = 1521
    
    try:
        # Create a socket object
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Set a timeout of 5 seconds
        sock.settimeout(5)
        
        # Attempt to connect
        result = sock.connect_ex((host, port))
        
        if result == 0:
            print("Network connection successful - Port is open")
            print("Database server is reachable")
        else:
            print("Error: Cannot connect to the database server")
            print("Possible causes:")
            print("1. Database server is not running")
            print("2. Firewall is blocking the connection")
            print("3. Network connectivity issues")
            print("4. Incorrect host or port")
        
    except socket.gaierror:
        print("Error: Could not resolve hostname")
    except socket.error as e:
        print(f"Socket error: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    print("Testing network connectivity to database server...")
    print(f"Host: 10.124.7.18")
    print(f"Port: 1521")
    print("-" * 50)
    test_network_connection() 