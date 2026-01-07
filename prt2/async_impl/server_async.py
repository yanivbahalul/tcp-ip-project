import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, Set, Callable, Optional
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import config
from utils import logger

config.load_config()

HOST = config.get_server_host()
PORT = config.get_server_port()
MAX_MESSAGE_SIZE = config.get_max_message_size()
READ_TIMEOUT = config.get_read_timeout()
MAX_NAME_LENGTH = config.get_max_name_length()
RATE_LIMIT_MSGS, RATE_LIMIT_WINDOW = config.get_rate_limit()

connected_clients: Set[asyncio.StreamWriter] = set()
client_info: Dict[asyncio.StreamWriter, dict] = {}
clients_by_name: Dict[str, asyncio.StreamWriter] = {}
client_chats: Dict[asyncio.StreamWriter, asyncio.StreamWriter] = {}
groups: Dict[str, Set[asyncio.StreamWriter]] = {}  # group_name -> set of writers
client_groups: Dict[asyncio.StreamWriter, Set[str]] = {}  # writer -> set of group names
message_log: list = []
client_rate_limits: Dict[asyncio.StreamWriter, deque] = {}

log_callback: Optional[Callable[[str], None]] = None

logger.setup_logger("tcp_server", config.get_log_level())
log = logger.get_logger()


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    addr = writer.get_extra_info('peername')
    client_id = f"{addr[0]}:{addr[1]}"
    client_name = None
    
    connected_clients.add(writer)
    client_info[writer] = {
        'address': addr,
        'client_id': client_id,
        'name': None,
        'connected_at': datetime.now().isoformat(),
        'messages_sent': 0,
        'messages_received': 0,
        'chat_partner': None,
        'groups': set()
    }
    client_groups[writer] = set()
    
    log_msg = f"Client connected: {client_id}"
    log.info(log_msg)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {log_msg}")
    if log_callback:
        log_callback(log_msg)
    
    client_rate_limits[writer] = deque()
    
    try:
        welcome = "welcome\nPlease send your name:\n"
        writer.write(welcome.encode('utf-8'))
        await writer.drain()
        
        try:
            name_data = await asyncio.wait_for(reader.read(1024), timeout=READ_TIMEOUT)
        except asyncio.TimeoutError:
            log_msg = f"Client {client_id} timed out while sending name"
            log.warning(log_msg)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {log_msg}")
            if log_callback:
                log_callback(log_msg)
            return
        if not name_data:
            return
        
        client_name = name_data.decode("utf-8").strip()
        
        if not client_name:
            error_msg = "ERROR: Name validation failed - Name cannot be empty. Please provide a valid name.\n"
            log.warning(f"Client {client_id} attempted to register with empty name")
            writer.write(error_msg.encode('utf-8'))
            await writer.drain()
            return
        
        if len(client_name) > MAX_NAME_LENGTH:
            error_msg = f"ERROR: Name validation failed - Name too long. Maximum length is {MAX_NAME_LENGTH} characters (received {len(client_name)}).\n"
            log.warning(f"Client {client_id} attempted to register with name too long: {len(client_name)} chars")
            writer.write(error_msg.encode('utf-8'))
            await writer.drain()
            return
        
        if '\n' in client_name or '\r' in client_name:
            error_msg = "ERROR: Name validation failed - Name contains invalid characters (newline/carriage return). Please use only printable characters.\n"
            log.warning(f"Client {client_id} attempted to register with invalid characters in name")
            writer.write(error_msg.encode('utf-8'))
            await writer.drain()
            return
        
        if client_name in clients_by_name:
            error_msg = f"ERROR: Name registration failed - The name '{client_name}' is already in use by another client. Please choose a different name.\n"
            log.warning(f"Client {client_id} attempted to register with duplicate name: {client_name}")
            writer.write(error_msg.encode('utf-8'))
            await writer.drain()
            return
        
        clients_by_name[client_name] = writer
        client_info[writer]['name'] = client_name
        
        log_msg = f"Client {client_id} registered as: {client_name}"
        log.info(log_msg)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {log_msg}")
        if log_callback:
            log_callback(log_msg)
        
        # Notify all other clients that a new user has connected
        notification_msg = f"USER_CONNECTED:{client_name}\n"
        for other_writer in list(connected_clients):
            if other_writer != writer and other_writer in connected_clients:
                try:
                    other_writer.write(notification_msg.encode('utf-8'))
                    await other_writer.drain()
                except Exception as e:
                    log.warning(f"Failed to notify client about new user connection: {e}")
        
        name_ack = f"Name registered: {client_name}\nCommands: CONNECT:name, DISCONNECT_CHAT, CREATE_GROUP:name, JOIN_GROUP:name, LEAVE_GROUP:name, LIST_GROUPS, LIST_USERS, GROUP:group_name:message\n"
        writer.write(name_ack.encode('utf-8'))
        await writer.drain()
        
        while True:
            try:
                data = await reader.read(MAX_MESSAGE_SIZE)
            except Exception as e:
                log_msg = f"Client {client_name} ({client_id}) connection error: {type(e).__name__}"
                log.warning(log_msg)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {log_msg}")
                if log_callback:
                    log_callback(log_msg)
                break
            if not data:
                break
            
            if len(data) >= MAX_MESSAGE_SIZE:
                error_msg = f"ERROR: Message size validation failed - Message exceeds maximum size of {MAX_MESSAGE_SIZE} bytes (received {len(data)} bytes). Please send a shorter message.\n"
                log.warning(f"Client {client_name} ({client_id}) sent message exceeding size limit: {len(data)} bytes")
                try:
                    writer.write(error_msg.encode('utf-8'))
                    await writer.drain()
                except:
                    pass
                continue
            
            data_decoded = data.decode("utf-8").strip()
            timestamp = datetime.now().isoformat()
            
            now = datetime.now().timestamp()
            rate_queue = client_rate_limits.get(writer, deque())
            
            while rate_queue and rate_queue[0] < now - RATE_LIMIT_WINDOW:
                rate_queue.popleft()
            
            if len(rate_queue) >= RATE_LIMIT_MSGS:
                error_msg = f"ERROR: Rate limit exceeded. Maximum {RATE_LIMIT_MSGS} messages per {RATE_LIMIT_WINDOW} seconds.\n"
                log.warning(f"Rate limit exceeded for client {client_name} ({client_id})")
                try:
                    writer.write(error_msg.encode('utf-8'))
                    await writer.drain()
                except:
                    pass
                continue
            
            rate_queue.append(now)
            client_rate_limits[writer] = rate_queue
            
            client_info[writer]['messages_received'] += 1
            
            # Skip logging for repeated requests (LIST_USERS, LIST_GROUPS)
            skip_logging = data_decoded == "LIST_USERS" or data_decoded == "LIST_GROUPS"
            
            if not skip_logging:
                log_entry = {
                    'timestamp': timestamp,
                    'client_id': client_id,
                    'client_name': client_name,
                    'direction': 'received',
                    'message': data_decoded
                }
                message_log.append(log_entry)
                
                log_msg = f"Received from {client_name} ({client_id}): {data_decoded}"
                log.debug(log_msg)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {log_msg}")
                if log_callback:
                    log_callback(log_msg)
            
            try:
                if data_decoded == "LIST_USERS":
                    user_list = list(clients_by_name.keys())
                    user_list_str = f"Connected users ({len(user_list)}): {', '.join(user_list)}\n"
                    writer.write(user_list_str.encode('utf-8'))
                    await writer.drain()
                    continue
                
                elif data_decoded == "LIST_GROUPS":
                    group_list = list(groups.keys())
                    if not group_list:
                        group_list_str = "No groups available\n"
                    else:
                        group_info = []
                        for group_name in group_list:
                            member_count = len(groups[group_name])
                            member_names = [client_info[w].get('name', 'Unknown') for w in groups[group_name] if w in client_info]
                            group_info.append(f"{group_name} ({member_count} members: {', '.join(member_names)})")
                        group_list_str = f"Available groups ({len(group_list)}):\n" + "\n".join(group_info) + "\n"
                    writer.write(group_list_str.encode('utf-8'))
                    await writer.drain()
                    continue
                
                elif data_decoded.startswith("CREATE_GROUP:"):
                    group_name = data_decoded[13:].strip()
                    
                    if not group_name:
                        error_msg = "ERROR: Group name cannot be empty\n"
                        writer.write(error_msg.encode('utf-8'))
                        await writer.drain()
                        continue
                    
                    if group_name in groups:
                        error_msg = f"ERROR: Group '{group_name}' already exists\n"
                        writer.write(error_msg.encode('utf-8'))
                        await writer.drain()
                        continue
                    
                    groups[group_name] = {writer}
                    client_groups[writer].add(group_name)
                    client_info[writer]['groups'].add(group_name)
                    
                    success_msg = f"Group '{group_name}' created. You are now a member.\n"
                    writer.write(success_msg.encode('utf-8'))
                    await writer.drain()
                    
                    # Notify all clients to refresh groups list
                    notification_msg = f"GROUP_UPDATED: {group_name} was created\n"
                    for other_writer in list(connected_clients):
                        if other_writer != writer and other_writer in connected_clients:
                            try:
                                other_writer.write(notification_msg.encode('utf-8'))
                                await other_writer.drain()
                            except:
                                pass
                    
                    log_msg = f"Group '{group_name}' created by {client_name}"
                    log.info(log_msg)
                    if log_callback:
                        log_callback(log_msg)
                    continue
                
                elif data_decoded.startswith("JOIN_GROUP:"):
                    group_name = data_decoded[11:].strip()
                    
                    if group_name not in groups:
                        error_msg = f"ERROR: Group '{group_name}' does not exist\n"
                        writer.write(error_msg.encode('utf-8'))
                        await writer.drain()
                        continue
                    
                    if writer in groups[group_name]:
                        error_msg = f"ERROR: You are already a member of group '{group_name}'\n"
                        writer.write(error_msg.encode('utf-8'))
                        await writer.drain()
                        continue
                    
                    groups[group_name].add(writer)
                    client_groups[writer].add(group_name)
                    client_info[writer]['groups'].add(group_name)
                    
                    success_msg = f"Joined group '{group_name}'\n"
                    writer.write(success_msg.encode('utf-8'))
                    await writer.drain()
                    
                    # Notify other group members
                    for member in groups[group_name]:
                        if member != writer and member in connected_clients:
                            try:
                                notify_msg = f"{client_name} joined group '{group_name}'\n"
                                member.write(notify_msg.encode('utf-8'))
                                await member.drain()
                            except:
                                pass
                    
                    # Notify all clients to refresh groups list
                    notification_msg = f"GROUP_UPDATED: {client_name} joined {group_name}\n"
                    for other_writer in list(connected_clients):
                        if other_writer != writer and other_writer in connected_clients:
                            try:
                                other_writer.write(notification_msg.encode('utf-8'))
                                await other_writer.drain()
                            except:
                                pass
                    
                    log_msg = f"{client_name} joined group '{group_name}'"
                    log.info(log_msg)
                    if log_callback:
                        log_callback(log_msg)
                    continue
                
                elif data_decoded.startswith("INVITE_TO_GROUP:"):
                    # Format: INVITE_TO_GROUP:group_name:user_name
                    parts = data_decoded[16:].split(":", 1)
                    if len(parts) != 2:
                        error_msg = "ERROR: Invalid INVITE_TO_GROUP format. Use: INVITE_TO_GROUP:group_name:user_name\n"
                        writer.write(error_msg.encode('utf-8'))
                        await writer.drain()
                        continue
                    
                    group_name = parts[0].strip()
                    invitee_name = parts[1].strip()
                    
                    # Check if group exists
                    if group_name not in groups:
                        error_msg = f"ERROR: Group '{group_name}' does not exist\n"
                        writer.write(error_msg.encode('utf-8'))
                        await writer.drain()
                        continue
                    
                    # Check if inviter is a member
                    if writer not in groups[group_name]:
                        error_msg = f"ERROR: You are not a member of group '{group_name}'\n"
                        writer.write(error_msg.encode('utf-8'))
                        await writer.drain()
                        continue
                    
                    # Check if invitee exists
                    if invitee_name not in clients_by_name:
                        error_msg = f"ERROR: User '{invitee_name}' is not connected\n"
                        writer.write(error_msg.encode('utf-8'))
                        await writer.drain()
                        continue
                    
                    invitee_writer = clients_by_name[invitee_name]
                    
                    # Check if invitee is already in group
                    if invitee_writer in groups[group_name]:
                        error_msg = f"ERROR: User '{invitee_name}' is already a member of group '{group_name}'\n"
                        writer.write(error_msg.encode('utf-8'))
                        await writer.drain()
                        continue
                    
                    # Add invitee to group
                    groups[group_name].add(invitee_writer)
                    client_groups[invitee_writer].add(group_name)
                    client_info[invitee_writer]['groups'].add(group_name)
                    
                    # Notify invitee
                    invite_msg = f"You were added to group '{group_name}' by {client_name}\n"
                    invitee_writer.write(invite_msg.encode('utf-8'))
                    await invitee_writer.drain()
                    
                    # Notify other group members
                    for member in groups[group_name]:
                        if member != writer and member != invitee_writer and member in connected_clients:
                            try:
                                notify_msg = f"{invitee_name} was added to group '{group_name}' by {client_name}\n"
                                member.write(notify_msg.encode('utf-8'))
                                await member.drain()
                            except:
                                pass
                    
                    # Notify all clients to refresh groups list
                    notification_msg = f"GROUP_UPDATED: {invitee_name} was added to {group_name}\n"
                    for other_writer in list(connected_clients):
                        if other_writer != writer and other_writer != invitee_writer and other_writer in connected_clients:
                            try:
                                other_writer.write(notification_msg.encode('utf-8'))
                                await other_writer.drain()
                            except:
                                pass
                    
                    success_msg = f"User '{invitee_name}' was added to group '{group_name}'\n"
                    writer.write(success_msg.encode('utf-8'))
                    await writer.drain()
                    
                    log_msg = f"{client_name} added {invitee_name} to group '{group_name}'"
                    log.info(log_msg)
                    if log_callback:
                        log_callback(log_msg)
                    continue
                
                elif data_decoded.startswith("LEAVE_GROUP:"):
                    group_name = data_decoded[12:].strip()
                    
                    if group_name not in groups:
                        error_msg = f"ERROR: Group '{group_name}' does not exist\n"
                        writer.write(error_msg.encode('utf-8'))
                        await writer.drain()
                        continue
                    
                    if writer not in groups[group_name]:
                        error_msg = f"ERROR: You are not a member of group '{group_name}'\n"
                        writer.write(error_msg.encode('utf-8'))
                        await writer.drain()
                        continue
                    
                    groups[group_name].discard(writer)
                    client_groups[writer].discard(group_name)
                    client_info[writer]['groups'].discard(group_name)
                    
                    # Remove group if empty
                    if not groups[group_name]:
                        del groups[group_name]
                        success_msg = f"Left group '{group_name}' (group removed as it's now empty)\n"
                    else:
                        success_msg = f"Left group '{group_name}'\n"
                    # Notify other group members
                    for member in groups[group_name]:
                        if member in connected_clients:
                            try:
                                notify_msg = f"{client_name} left group '{group_name}'\n"
                                member.write(notify_msg.encode('utf-8'))
                                await member.drain()
                            except:
                                pass
                    
                    # Notify all clients to refresh groups list
                    notification_msg = f"GROUP_UPDATED: {client_name} left {group_name}\n"
                    for other_writer in list(connected_clients):
                        if other_writer != writer and other_writer in connected_clients:
                            try:
                                other_writer.write(notification_msg.encode('utf-8'))
                                await other_writer.drain()
                            except:
                                pass
                    
                    writer.write(success_msg.encode('utf-8'))
                    await writer.drain()
                    
                    log_msg = f"{client_name} left group '{group_name}'"
                    log.info(log_msg)
                    if log_callback:
                        log_callback(log_msg)
                    continue
                
                elif data_decoded.startswith("GROUP:"):
                    # Format: GROUP:group_name:message
                    parts = data_decoded[6:].split(":", 1)
                    if len(parts) != 2:
                        error_msg = "ERROR: Invalid GROUP format. Use: GROUP:group_name:message\n"
                        writer.write(error_msg.encode('utf-8'))
                        await writer.drain()
                        continue
                    
                    group_name = parts[0].strip()
                    group_message = parts[1].strip()
                    
                    if group_name not in groups:
                        error_msg = f"ERROR: Group '{group_name}' does not exist\n"
                        writer.write(error_msg.encode('utf-8'))
                        await writer.drain()
                        continue
                    
                    if writer not in groups[group_name]:
                        error_msg = f"ERROR: You are not a member of group '{group_name}'\n"
                        writer.write(error_msg.encode('utf-8'))
                        await writer.drain()
                        continue
                    
                    # Send message to all group members except sender
                    forward_msg = f"[{group_name}] {client_name}: {group_message}\n"
                    sent_count = 0
                    for member in groups[group_name]:
                        if member != writer and member in connected_clients:
                            try:
                                member.write(forward_msg.encode('utf-8'))
                                await member.drain()
                                sent_count += 1
                                if member in client_info:
                                    client_info[member]['messages_received'] += 1
                            except:
                                pass
                    
                    if sent_count > 0:
                        success_msg = f"Message sent to {sent_count} member(s) in group '{group_name}'\n"
                    else:
                        success_msg = f"Message sent to group '{group_name}' (no other members online)\n"
                    
                    writer.write(success_msg.encode('utf-8'))
                    await writer.drain()
                    
                    client_info[writer]['messages_sent'] += sent_count
                    
                    log_entry = {
                        'timestamp': timestamp,
                        'client_id': client_id,
                        'client_name': client_name,
                        'direction': 'sent',
                        'message': f"Group message to {group_name}: {group_message}"
                    }
                    message_log.append(log_entry)
                    
                    log_msg = f"Group message from {client_name} to {group_name} ({sent_count} recipients)"
                    log.debug(log_msg)
                    if log_callback:
                        log_callback(log_msg)
                    continue
                
                elif data_decoded.startswith("CONNECT:"):
                    target_name = data_decoded[8:].strip()
                    
                    if target_name == client_name:
                        error_msg = "ERROR: Connection failed - You cannot connect to yourself. Please specify a different client name.\n"
                        log.debug(f"Client {client_name} attempted to connect to themselves")
                        writer.write(error_msg.encode('utf-8'))
                        await writer.drain()
                        continue
                    
                    if target_name not in clients_by_name:
                        error_msg = f"ERROR: Connection failed - Client '{target_name}' not found. The client may not be connected or the name is incorrect. Use available client names.\n"
                        log.warning(f"Client {client_name} attempted to connect to non-existent client: {target_name}")
                        writer.write(error_msg.encode('utf-8'))
                        await writer.drain()
                        continue
                    
                    target_writer = clients_by_name[target_name]
                    
                    if target_writer not in connected_clients:
                        error_msg = f"ERROR: Connection failed - Client '{target_name}' is no longer connected. The client may have disconnected.\n"
                        log.warning(f"Client {client_name} attempted to connect to disconnected client: {target_name}")
                        writer.write(error_msg.encode('utf-8'))
                        await writer.drain()
                        continue
                    
                    if client_info[writer].get('chat_partner') == target_writer:
                        error_msg = f"ERROR: Connection failed - You are already connected to '{target_name}'. No need to reconnect.\n"
                        log.debug(f"Client {client_name} attempted to reconnect to {target_name}")
                        writer.write(error_msg.encode('utf-8'))
                        await writer.drain()
                        continue
                    
                    # Close any existing chat connection before opening new one
                    if writer in client_chats:
                        old_partner = client_chats[writer]
                        # Notify old partner that chat was closed
                        if old_partner in client_info and old_partner in connected_clients:
                            try:
                                old_partner_name = client_info[old_partner].get('name', 'Unknown')
                                disconnect_msg = f"[System] {client_name} ended the chat to start a new one. The chat session has been closed.\n"
                                old_partner.write(disconnect_msg.encode('utf-8'))
                                await old_partner.drain()
                                client_info[old_partner]['chat_partner'] = None
                            except:
                                pass
                        if old_partner in client_info:
                            client_info[old_partner]['chat_partner'] = None
                        if old_partner in client_chats and client_chats[old_partner] == writer:
                            del client_chats[old_partner]
                    
                    client_chats[writer] = target_writer
                    client_info[writer]['chat_partner'] = target_writer
                    client_info[target_writer]['chat_partner'] = writer
                    
                    success_msg = f"Connected to {target_name}. You can now send messages directly.\n"
                    writer.write(success_msg.encode('utf-8'))
                    await writer.drain()
                    
                    target_msg = f"{client_name} connected to you. You can now send messages directly.\n"
                    target_writer.write(target_msg.encode('utf-8'))
                    await target_writer.drain()
                    
                    log_msg = f"Chat opened between {client_name} and {target_name}"
                    log.info(log_msg)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {log_msg}")
                    if log_callback:
                        log_callback(log_msg)
                    
                elif data_decoded == "DISCONNECT_CHAT":
                    # Close current chat connection without disconnecting from server
                    if writer in client_chats:
                        old_partner = client_chats[writer]
                        # Notify partner that chat was closed
                        if old_partner in client_info and old_partner in connected_clients:
                            try:
                                partner_name = client_info[old_partner].get('name', 'Unknown')
                                disconnect_msg = f"[System] {client_name} ended the chat. The chat session has been closed.\n"
                                old_partner.write(disconnect_msg.encode('utf-8'))
                                await old_partner.drain()
                                client_info[old_partner]['chat_partner'] = None
                            except:
                                pass
                        if old_partner in client_info:
                            client_info[old_partner]['chat_partner'] = None
                        if old_partner in client_chats and client_chats[old_partner] == writer:
                            del client_chats[old_partner]
                        del client_chats[writer]
                        client_info[writer]['chat_partner'] = None
                        
                        success_msg = "Chat disconnected successfully. You can start a new chat with CONNECT:name\n"
                        writer.write(success_msg.encode('utf-8'))
                        await writer.drain()
                        
                        log_msg = f"{client_name} disconnected from chat"
                        log.info(log_msg)
                        if log_callback:
                            log_callback(log_msg)
                    else:
                        # Not in any chat
                        error_msg = "ERROR: You are not in any chat. Use CONNECT:name to start a chat.\n"
                        writer.write(error_msg.encode('utf-8'))
                        await writer.drain()
                    continue
                    
                elif client_info[writer].get('chat_partner'):
                    target_writer = client_info[writer]['chat_partner']
                    
                    if target_writer not in connected_clients:
                        error_msg = "ERROR: Message delivery failed - Your chat partner has disconnected. The chat session has been closed.\n"
                        log.warning(f"Client {client_name} attempted to send message to disconnected partner")
                        writer.write(error_msg.encode('utf-8'))
                        await writer.drain()
                        client_info[writer]['chat_partner'] = None
                        if writer in client_chats:
                            del client_chats[writer]
                        continue
                    
                    target_name = client_info[target_writer].get('name', 'Unknown')
                    
                    forward_msg = f"[{client_name}]: {data_decoded}\n"
                    try:
                        target_writer.write(forward_msg.encode('utf-8'))
                        await target_writer.drain()
                    except (ConnectionResetError, BrokenPipeError, OSError) as e:
                        error_msg = "ERROR: Message delivery failed - Chat partner disconnected during message transmission. The chat session has been closed.\n"
                        log.error(f"Error forwarding message from {client_name} to {target_name}: {type(e).__name__}")
                        writer.write(error_msg.encode('utf-8'))
                        await writer.drain()
                        client_info[writer]['chat_partner'] = None
                        if target_writer in client_info:
                            client_info[target_writer]['chat_partner'] = None
                        if writer in client_chats:
                            del client_chats[writer]
                        continue
                    
                    client_info[writer]['messages_sent'] += 1
                    client_info[target_writer]['messages_received'] += 1
                    
                    log_entry = {
                        'timestamp': timestamp,
                        'client_id': client_info[target_writer]['client_id'],
                        'client_name': target_name,
                        'direction': 'received',
                        'message': f"Forwarded from {client_name}: {data_decoded}"
                    }
                    message_log.append(log_entry)
                    
                    log_msg = f"Message forwarded from {client_name} to {target_name}"
                    log.debug(log_msg)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {log_msg}")
                    if log_callback:
                        log_callback(log_msg)
                    
                else:
                    response = f"server received {data_decoded.upper()}\n"
                    writer.write(response.encode('utf-8'))
                    await writer.drain()
                    
                    client_info[writer]['messages_sent'] += 1
                    
                    log_entry = {
                        'timestamp': timestamp,
                        'client_id': client_id,
                        'client_name': client_name,
                        'direction': 'sent',
                        'message': response.strip()
                    }
                    message_log.append(log_entry)
                    
            except (ConnectionResetError, BrokenPipeError, OSError) as e:
                log_msg = f"Client {client_name} ({client_id}) closed connection before response sent: {type(e).__name__}"
                log.warning(log_msg)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {log_msg}")
                if log_callback:
                    log_callback(log_msg)
                break
            
    except (ConnectionResetError, BrokenPipeError, asyncio.IncompleteReadError) as e:
        log_msg = f"Client disconnected: {client_id} - {type(e).__name__}"
        log.info(log_msg)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {log_msg}")
        if log_callback:
            log_callback(log_msg)
        # Notify chat partner immediately when user disconnects
        # Try to find partner from client_chats first, then from chat_partner
        partner = None
        if writer in client_chats:
            partner = client_chats[writer]
        elif writer in client_info and client_info[writer].get('chat_partner'):
            partner = client_info[writer]['chat_partner']
        
        if partner and partner in client_info and partner in connected_clients:
            try:
                disconnect_msg = f"[System] {client_name} has disconnected. You can no longer send messages to them.\n"
                partner.write(disconnect_msg.encode('utf-8'))
                await partner.drain()
                client_info[partner]['chat_partner'] = None
            except:
                pass
        
        if partner and partner in client_info:
            client_info[partner]['chat_partner'] = None
        
        # Clean up client_chats and client_info
        if writer in client_chats:
            if client_chats[writer] in client_chats and client_chats[client_chats[writer]] == writer:
                del client_chats[client_chats[writer]]
            del client_chats[writer]
    except Exception as e:
        log_msg = f"Error with client {client_id}: {e}"
        log.error(log_msg, exc_info=True)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {log_msg}")
        if log_callback:
            log_callback(log_msg)
        # Notify chat partner immediately when error occurs
        # Try to find partner from client_chats first, then from chat_partner
        partner = None
        if writer in client_chats:
            partner = client_chats[writer]
        elif writer in client_info and client_info[writer].get('chat_partner'):
            partner = client_info[writer]['chat_partner']
        
        if partner and partner in client_info and partner in connected_clients:
            try:
                disconnect_msg = f"[System] {client_name} has disconnected. You can no longer send messages to them.\n"
                partner.write(disconnect_msg.encode('utf-8'))
                await partner.drain()
                client_info[partner]['chat_partner'] = None
            except:
                pass
        
        if partner and partner in client_info:
            client_info[partner]['chat_partner'] = None
        
        # Clean up client_chats and client_info
        if writer in client_chats:
            if client_chats[writer] in client_chats and client_chats[client_chats[writer]] == writer:
                del client_chats[client_chats[writer]]
            del client_chats[writer]
    finally:
        # Cleanup: notify chat partner if not already notified (backup)
        # Try to find partner from client_chats first, then from chat_partner
        partner = None
        if writer in client_chats:
            partner = client_chats[writer]
        elif writer in client_info and client_info[writer].get('chat_partner'):
            partner = client_info[writer]['chat_partner']
        
        if partner and partner in client_info and partner in connected_clients:
            try:
                disconnect_msg = f"[System] {client_name} has disconnected. You can no longer send messages to them.\n"
                partner.write(disconnect_msg.encode('utf-8'))
                await partner.drain()
                client_info[partner]['chat_partner'] = None
            except:
                pass
        
        if partner and partner in client_info:
            client_info[partner]['chat_partner'] = None
        
        # Clean up client_chats and client_info
        if writer in client_chats:
            if client_chats[writer] in client_chats and client_chats[client_chats[writer]] == writer:
                del client_chats[client_chats[writer]]
            del client_chats[writer]
        
        if client_name and client_name in clients_by_name:
            del clients_by_name[client_name]
        
        # Remove from all groups
        if writer in client_groups:
            groups_to_remove = list(client_groups[writer])
            for group_name in groups_to_remove:
                if group_name in groups:
                    groups[group_name].discard(writer)
                    if not groups[group_name]:
                        del groups[group_name]
            del client_groups[writer]
        
        if writer in connected_clients:
            connected_clients.remove(writer)
        if writer in client_info:
            del client_info[writer]
        
        if writer in client_rate_limits:
            del client_rate_limits[writer]
        
        writer.close()
        await writer.wait_closed()
        
        log_msg = f"Client {client_name or client_id} ({client_id}) cleaned up"
        log.info(log_msg)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {log_msg}")
        if log_callback:
            log_callback(log_msg)


async def start_server(host=None, port=None):
    server_host = host if host is not None else HOST
    server_port = port if port is not None else PORT
    server = await asyncio.start_server(handle_client, server_host, server_port)
    addr = server.sockets[0].getsockname()
    log_msg = f"Server listening on {addr[0]}:{addr[1]}"
    log.info(log_msg)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {log_msg}")
    if log_callback:
        log_callback(log_msg)
    
    async with server:
        await server.serve_forever()


def set_log_callback(callback: Callable[[str], None]):
    global log_callback
    log_callback = callback


def get_statistics():
    total_messages = len(message_log)
    received = sum(1 for msg in message_log if msg['direction'] == 'received')
    sent = sum(1 for msg in message_log if msg['direction'] == 'sent')
    
    # Build chat connections mapping
    chat_connections = {}  # client_id -> partner_name
    for writer, info in client_info.items():
        if info.get('chat_partner'):
            partner_writer = info['chat_partner']
            if partner_writer in client_info:
                partner_name = client_info[partner_writer].get('name', 'Unknown')
                chat_connections[info['client_id']] = partner_name
    
    clients_info_dict = {}
    for info in client_info.values():
        client_id = info['client_id']
        partner_writer = info.get('chat_partner')
        partner_name = None
        if partner_writer and partner_writer in client_info:
            partner_name = client_info[partner_writer].get('name', 'Unknown')
        
        clients_info_dict[client_id] = {
            'address': info['address'],
            'name': info.get('name', 'Unknown'),
            'connected_at': info['connected_at'],
            'messages_sent': info['messages_sent'],
            'messages_received': info['messages_received'],
            'chat_partner': info.get('chat_partner') is not None,
            'chat_partner_name': partner_name,
            'groups': list(info.get('groups', set()))
        }
    
    return {
        'connected_clients': len(connected_clients),
        'total_messages': total_messages,
        'messages_received': received,
        'messages_sent': sent,
        'clients_info': clients_info_dict,
        'groups': {group_name: [client_info[w].get('name', 'Unknown') for w in group_members if w in client_info] 
                  for group_name, group_members in groups.items()},
        'chat_connections': chat_connections
    }


def export_logs(filename: str = None):
    if filename is None:
        filename = f"server_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(message_log, f, indent=2, ensure_ascii=False)
    
    return filename


if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Server shutting down...")
        if message_log:
            export_logs()
            print(f"Logs exported to server_logs_*.json")

