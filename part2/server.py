import socket
import threading

DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 10000
BUFFER_SIZE = 1024
ENCODING = 'utf-8'

class ServerLogic:
    """Central server managing client connections and message routing"""

    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.bind_host = host
        self.bind_port = port
        self.server_socket = None
        self.connected_clients = {}
        self.is_running = False
        self.log_callback = None

    def log(self, message):
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def parse_chat_message(self, message, sender_nickname):
        result = {"target": None, "content": None, "error": None}
        try:
            parts = message.split(":", 1)
            target = parts[0].strip()
            content = parts[1].strip()

            if target == sender_nickname:
                result["error"] = "Cannot send message to yourself."
            elif not target or not content:
                result["error"] = "Name or message cannot be empty."
            else:
                result["target"] = target
                result["content"] = content

        except IndexError:
            result["error"] = "Invalid format. Use 'name:message'."
        except Exception:
            result["error"] = "Message parsing error."

        return result

    def get_valid_nickname(self, client_socket):
        FORBIDDEN_NAMES = {"SYSTEM", "ERROR", "ONLINE_USERS", "", "SERVER"} | {user.upper() for user in list(self.connected_clients)}

        try:
            nickname = client_socket.recv(BUFFER_SIZE).decode(ENCODING).strip()

            if not nickname:
                client_socket.send("ERROR: Nickname cannot be empty.".encode(ENCODING))
                return None

            if nickname.upper() in FORBIDDEN_NAMES:
                client_socket.send("ERROR: Nickname taken or forbidden.".encode(ENCODING))
                return None

            return nickname

        except:
            return None

    def close_connection(self, nickname):
        if nickname not in self.connected_clients:
            return
        client_socket = self.connected_clients.pop(nickname)
        try:
            client_socket.close()
            self.log(f"Connection closed: {nickname}")
        except Exception as e:
            self.log(f"Error closing connection for {nickname}: {e}")

    def broadcast_online_users(self):
        user_list_msg = "ONLINE_USERS:" + ",".join(self.connected_clients.keys())
        for client_name in list(self.connected_clients.keys()):
            try:
                self.connected_clients[client_name].send(user_list_msg.encode(ENCODING))
            except:
                self.close_connection(client_name)

    def kick_client(self, nickname):
        self.close_connection(nickname)
        self.broadcast_online_users()

    def get_online_users(self):
        user_list = []
        for nickname, socket_obj in self.connected_clients.items():
            try:
                client_address = socket_obj.getpeername()
                user_list.append({"nickname": nickname, "address": client_address})
            except:
                user_list.append({"nickname": nickname, "address": None})
        return user_list

    def handle_client(self, client_socket, nickname):
        while self.is_running:
            try:
                received_message = client_socket.recv(BUFFER_SIZE).decode(ENCODING)
                if not received_message:
                    self.log(f"Connection closed by {nickname}")
                    break

                parsed_result = self.parse_chat_message(received_message, nickname)

                if parsed_result["error"]:
                    client_socket.send(f"System: {parsed_result['error']}".encode(ENCODING))
                    continue

                recipient_name, message_text = parsed_result["target"], parsed_result["content"]

                if recipient_name not in self.connected_clients:
                    client_socket.send(f"System: User '{recipient_name}' not found.".encode(ENCODING))
                    continue

                recipient_socket = self.connected_clients[recipient_name]
                try:
                    recipient_socket.send(f"[{nickname}]: {message_text}".encode(ENCODING))
                except (socket.error, BrokenPipeError):
                    self.log(f"Client {recipient_name} disconnected")
                    self.kick_client(recipient_name)
                    client_socket.send(f"System: {recipient_name} is no longer online.".encode(ENCODING))

            except (ConnectionResetError, socket.error):
                break

        self.kick_client(nickname)

    def start(self, on_log=None):
        if on_log:
            self.log_callback = on_log

        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((self.bind_host, self.bind_port))
            self.server_socket.listen(10)
            self.is_running = True

            self.log(f"Server started on {self.bind_host}:{self.bind_port}")
            self.log("Waiting for connections...")

            while self.is_running:
                try:
                    client_socket, client_address = self.server_socket.accept()

                    user_nickname = self.get_valid_nickname(client_socket)

                    if not user_nickname:
                        client_socket.close()
                        continue

                    self.connected_clients[user_nickname] = client_socket
                    self.log(f"New user: {user_nickname} from {client_address}")
                    client_socket.send("OK: Welcome".encode(ENCODING))

                    self.broadcast_online_users()

                    threading.Thread(target=self.handle_client,
                                     args=(client_socket, user_nickname),
                                     daemon=True).start()

                except Exception as e:
                    if self.is_running:
                        self.log(f"Server error: {e}")
                    break

        except Exception as e:
            self.log(f"Critical error: Failed to bind port. {e}")
            return False, str(e)

        return True, "Server started"

    def start_async(self, on_log=None):
        threading.Thread(target=self.start, args=(on_log,), daemon=True).start()

    def stop(self):
        self.is_running = False
        for nickname in list(self.connected_clients.keys()):
            self.close_connection(nickname)
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

def run_cli_mode():
    host = input(f"Host IP (default {DEFAULT_HOST}): ").strip() or DEFAULT_HOST
    port_input = input(f"Port (default {DEFAULT_PORT}): ").strip() or str(DEFAULT_PORT)
    try:
        port = int(port_input)
    except ValueError:
        print("Invalid port.")
        return

    server_instance = ServerLogic(host, port)
    print(f"Starting server on {host}:{port}...")
    try:
        server_instance.start()
    except KeyboardInterrupt:
        server_instance.stop()

if __name__ == "__main__":
    run_cli_mode()
