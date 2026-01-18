import socket
import threading
import sys

HOST = '127.0.0.1'
PORT = 55555
BUFFER_SIZE = 1024
ENCODING = 'utf-8'

class ChatLogic:

    def __init__(self, host=HOST, port=PORT):
        self.server_host = host
        self.server_port = port
        self.socket_connection = None
        self.user_alias = ""
        self.is_connected = False

    def connect(self, nickname):
        try:
            self.socket_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_connection.connect((self.server_host, self.server_port))

            self.socket_connection.send(nickname.encode(ENCODING))
            server_response = self.socket_connection.recv(BUFFER_SIZE).decode(ENCODING)

            if not server_response:
                self.socket_connection.close()
                return False, "Connection closed by server."

            if server_response.startswith("ERROR:"):
                error_message = server_response.replace("ERROR:", "").strip()
                self.socket_connection.close()
                return False, error_message

            self.user_alias = nickname
            self.is_connected = True
            return True, "Connected successfully"

        except Exception as e:
            if self.socket_connection:
                try:
                    self.socket_connection.close()
                except: pass
            return False, str(e)

    def disconnect(self):
        """Close connection cleanly"""
        self.is_connected = False
        try:
            if self.socket_connection:
                self.socket_connection.close()
        except:
            pass

    def send_private_message(self, target, message):
        """Send private message in 'target:message' format"""
        try:
            if not self.is_connected: return
            formatted_message = f"{target}:{message}"
            self.socket_connection.send(formatted_message.encode(ENCODING))
        except socket.error:
            print("Failed to send message. Connection lost.")
            self.disconnect()

    def start_receiving(self, callback):
        """Start background thread to receive messages"""
        def receive_loop():
            while self.is_connected:
                try:
                    received_data = self.socket_connection.recv(BUFFER_SIZE).decode(ENCODING)
                    if not received_data:
                        break
                    callback(received_data)
                except:
                    break

            self.disconnect()
            callback("System: Disconnected from server.")

        threading.Thread(target=receive_loop, daemon=True).start()

def run_cli_mode():
    host = input(f"Host IP (default {PORT}): ").strip() or HOST
    port_input = input(f"Port (default {PORT}): ").strip() or str(HOST)

    try:
        port = int(port_input)
    except ValueError:
        print("Invalid port.")
        return

    logic = None

    while True:
        nickname = input("Choose a nickname: ").strip()
        if not nickname:
            print("Nickname cannot be empty.")
            continue

        chat_client = ChatLogic(host, port)
        connection_result, response_message = chat_client.connect(nickname)

        if connection_result:
            print(f"Connected as {chat_client.user_alias}! Usage: 'target:message'")
            print(f"Type 'exit' to quit.")
            break
        else:
            print(f"Connection failed: {response_message}")
            print("Please try again.\n")

    def cli_callback(message):
        print(f"\n{message}\n> ", end="")

    chat_client.start_receiving(cli_callback)

    while True:
        try:
            user_input = input("> ")
            if user_input.lower() == 'exit':
                chat_client.disconnect()
                break

            if ":" in user_input:
                recipient, message_content = user_input.split(":", 1)
                chat_client.send_private_message(recipient.strip(), message_content.strip())
            else:
                print("Invalid format! Use: target:message")

        except KeyboardInterrupt:
            chat_client.disconnect()
            break

if __name__ == "__main__":
    run_cli_mode()
