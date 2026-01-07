import socket 
import threading

HOST = "0.0.0.0"
PORT = 10000

def handle_client(conn, addr):
    print(f"client connected in: {addr}")
    try:
        welcome = "welcome"
        conn.sendall(welcome.encode('utf-8')) 

        while True:
            data = conn.recv(1024)
            if not data: 
                break

            data_d = data.decode("utf-8")
            print(f"got from client message: {addr} : {data_d}")
            response = f"server received {data_d.upper()}"
            conn.sendall(response.encode('utf-8'))

    except (ConnectionResetError, BrokenPipeError):
        print(f"client disconnected {addr}")
    
    finally:
        conn.close() 


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"Server listen in: {HOST}:{PORT}")

    while True:
        conn, addr = server_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(conn, addr))
        client_thread.start()
        print(f"client online {threading.active_count() - 1}") 

if __name__ == "__main__":
    start_server()