import asyncio
import sys
from datetime import datetime

HOST = "192.168.0.106"
PORT = 10000
MAX_MESSAGE_SIZE = 4096
READ_TIMEOUT = 30.0


async def chat_client(client_name: str):
    try:
        reader, writer = await asyncio.open_connection(HOST, PORT)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Connected to server at {HOST}:{PORT}")
        
        try:
            welcome_data = await asyncio.wait_for(reader.read(MAX_MESSAGE_SIZE), timeout=READ_TIMEOUT)
        except asyncio.TimeoutError:
            print("Timeout: Server did not respond")
            writer.close()
            await writer.wait_closed()
            return
        welcome = welcome_data.decode('utf-8').strip()
        print(f"Server: {welcome}")
        
        writer.write(f"{client_name}\n".encode('utf-8'))
        await writer.drain()
        
        try:
            name_response = await asyncio.wait_for(reader.read(MAX_MESSAGE_SIZE), timeout=READ_TIMEOUT)
        except asyncio.TimeoutError:
            print("Timeout: Server did not respond to name")
            writer.close()
            await writer.wait_closed()
            return
        name_resp = name_response.decode('utf-8').strip()
        print(f"Server: {name_resp}")
        
        if "ERROR" in name_resp:
            print("Failed to register name. Exiting.")
            writer.close()
            await writer.wait_closed()
            return
        
        async def read_messages():
            try:
                while True:
                    try:
                        data = await reader.read(MAX_MESSAGE_SIZE)
                    except Exception as e:
                        print(f"\nError reading messages: {e}")
                        break
                    if not data:
                        break
                    message = data.decode('utf-8').strip()
                    if message:
                        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {message}")
            except Exception as e:
                print(f"Error reading messages: {e}")
        
        read_task = asyncio.create_task(read_messages())
        
        print("\nCommands:")
        print("  CONNECT:name - Connect to another client")
        print("  Type message and press Enter to send")
        print("  Type 'quit' to exit\n")
        
        try:
            while True:
                user_input = await asyncio.to_thread(input, f"[{client_name}]> ")
                
                if user_input.lower() == 'quit':
                    break
                
                if user_input.strip():
                    message_with_newline = user_input + '\n'
                    writer.write(message_with_newline.encode('utf-8'))
                    await writer.drain()
        
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        except EOFError:
            pass
        
        read_task.cancel()
        try:
            await read_task
        except asyncio.CancelledError:
            pass
        
        writer.close()
        await writer.wait_closed()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Disconnected from server")
        
    except ConnectionRefusedError:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Connection failed: Server is not responding.")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] An error occurred: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        name = sys.argv[1]
    else:
        name = input("Enter your name: ").strip()
        if not name:
            print("Name cannot be empty!")
            sys.exit(1)
    
    try:
        asyncio.run(chat_client(name))
    except KeyboardInterrupt:
        print("\nExiting...")

