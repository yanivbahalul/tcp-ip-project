import socket
import csv

HOST = "192.168.0.106"
PORT = 10000
CSV_FILE = "group68_http_input.csv"

def start_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client_socket.connect((HOST, PORT))
        print(f"Connected to server at: {HOST}:{PORT}")
        
        welcome = client_socket.recv(1024).decode('utf-8')
        print(f"Server says: {welcome}")
        
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['src_app'] == 'client_browser' and row['dst_app'] == 'web_server':
                    message = row['message']
                    print(f"Sending: {message}")
                    
                    client_socket.sendall((message + '\n').encode('utf-8'))
                    
                    response = client_socket.recv(1024).decode('utf-8')
                    print(f"Server response: {response}")
            
    except ConnectionRefusedError:
        print("Connection failed: Server is not responding.")
    except FileNotFoundError:
        print(f"Error: CSV file '{CSV_FILE}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally: 
        client_socket.close()
        print("Connection closed.")

if __name__ == "__main__":
    start_client()