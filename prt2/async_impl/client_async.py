import asyncio
import csv
import json
import sys
import os
from datetime import datetime
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import config

config.load_config()

HOST = config.get_client_host()
PORT = config.get_client_port()
CSV_FILE = "../prt1/group68_http_input.csv"
MAX_MESSAGE_SIZE = config.get_max_message_size()
READ_TIMEOUT = config.get_read_timeout()

message_log: List[Dict] = []


async def send_message(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, 
                      message: str, msg_id: int = None):
    try:
        message_with_newline = message + '\n'
        writer.write(message_with_newline.encode('utf-8'))
        await writer.drain()
        
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'msg_id': msg_id,
            'direction': 'sent',
            'message': message
        }
        message_log.append(log_entry)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Sent (ID: {msg_id}): {message}")
        
        try:
            response_data = await asyncio.wait_for(reader.read(MAX_MESSAGE_SIZE), timeout=READ_TIMEOUT)
        except asyncio.TimeoutError:
            raise Exception("Timeout waiting for server response")
        response = response_data.decode('utf-8').strip()
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'msg_id': msg_id,
            'direction': 'received',
            'message': response
        }
        message_log.append(log_entry)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Received (ID: {msg_id}): {response}")
        
        return response
        
    except Exception as e:
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'msg_id': msg_id,
            'direction': 'error',
            'message': str(e)
        }
        message_log.append(error_entry)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Error (ID: {msg_id}): {e}")
        raise


async def send_messages_from_csv(csv_file: str = CSV_FILE, delay: float = 0.1):
    try:
        reader, writer = await asyncio.open_connection(HOST, PORT)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Connected to server at: {HOST}:{PORT}")
        
        try:
            welcome_data = await asyncio.wait_for(reader.read(MAX_MESSAGE_SIZE), timeout=READ_TIMEOUT)
        except asyncio.TimeoutError:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Timeout waiting for welcome message")
            writer.close()
            await writer.wait_closed()
            return
        welcome = welcome_data.decode('utf-8')
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Server says: {welcome}")
        
        messages_sent = 0
        messages_failed = 0
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader_csv = csv.DictReader(file)
                for row in reader_csv:
                    if row['src_app'] == 'client_browser' and row['dst_app'] == 'web_server':
                        message = row['message']
                        msg_id = int(row['msg_id'])
                        
                        try:
                            await send_message(reader, writer, message, msg_id)
                            messages_sent += 1
                            
                            if delay > 0:
                                await asyncio.sleep(delay)
                                
                        except Exception as e:
                            messages_failed += 1
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] Failed to send message {msg_id}: {e}")
                            continue
                            
        except FileNotFoundError:
            print(f"Error: CSV file '{csv_file}' not found.")
            return
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Summary:")
        print(f"  Messages sent successfully: {messages_sent}")
        print(f"  Messages failed: {messages_failed}")
        print(f"  Total messages in log: {len(message_log)}")
        
        writer.close()
        await writer.wait_closed()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Connection closed.")
        
    except ConnectionRefusedError:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Connection failed: Server is not responding.")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] An error occurred: {e}")


def get_statistics():
    sent = sum(1 for msg in message_log if msg['direction'] == 'sent')
    received = sum(1 for msg in message_log if msg['direction'] == 'received')
    errors = sum(1 for msg in message_log if msg['direction'] == 'error')
    
    return {
        'total_messages': len(message_log),
        'messages_sent': sent,
        'messages_received': received,
        'errors': errors
    }


def export_logs(filename: str = None):
    if filename is None:
        filename = f"client_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(message_log, f, indent=2, ensure_ascii=False)
    
    return filename


async def send_single_message(message: str):
    reader = None
    writer = None
    try:
        reader, writer = await asyncio.open_connection(HOST, PORT)
        
        try:
            welcome_data = await asyncio.wait_for(reader.read(MAX_MESSAGE_SIZE), timeout=READ_TIMEOUT)
        except asyncio.TimeoutError:
            raise Exception("Timeout waiting for welcome message")
        welcome = welcome_data.decode('utf-8').strip()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Server says: {welcome}")
        
        response = await send_message(reader, writer, message)
        
        writer.close()
        await writer.wait_closed()
        
        return response
        
    except Exception as e:
        print(f"Error sending message: {e}")
        if writer and not writer.is_closing():
            writer.close()
            try:
                await writer.wait_closed()
            except:
                pass
        raise


if __name__ == "__main__":
    try:
        asyncio.run(send_messages_from_csv())
        if message_log:
            export_logs()
            print(f"Logs exported to client_logs_*.json")
    except KeyboardInterrupt:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Interrupted by user")
        if message_log:
            export_logs()
            print(f"Logs exported to client_logs_*.json")

