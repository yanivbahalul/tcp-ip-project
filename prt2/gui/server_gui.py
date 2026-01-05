import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import asyncio
import threading
import json
from datetime import datetime
import sys
import os
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import async_impl.server_async as server_async

from gui.theme import COLORS, FONTS, SPACING, BORDER_RADIUS, get_button_colors


class ServerGUI:
    """GUI application for the chat server.
    
    Provides server control, statistics, and network visualization.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Async Server - GUI")
        self.root.geometry("900x700")
        self.root.configure(bg=COLORS['bg_main'])
        
        self.server_task = None
        self.server_running = False
        self.loop = None
        self.server_thread = None
        
        self.style = ttk.Style()
        self.configure_ttk_styles()
        
        self.clients = {}
        self.groups = {}
        self.client_circles = {}
        self.group_rects = {}
        self.connection_lines = {}
        
        self.create_widgets()
        
        self.update_statistics()
    
    def configure_ttk_styles(self):
        """Configure ttk widget styles to match theme."""
        btn_colors = get_button_colors('primary')
        self.style.configure('TButton',
                            background=btn_colors['bg'],
                            foreground=btn_colors['text'],
                            borderwidth=0,
                            focuscolor='none')
        self.style.map('TButton',
                      background=[('active', btn_colors['hover']),
                                 ('pressed', btn_colors['hover'])],
                      foreground=[('active', btn_colors['text']),
                                 ('pressed', btn_colors['text'])])
        
        self.style.configure('TLabelFrame',
                            background=COLORS['bg_main'],
                            foreground=COLORS['text_primary'],
                            borderwidth=1,
                            relief=tk.FLAT)
        self.style.configure('TLabelFrame.Label',
                            background=COLORS['bg_main'],
                            foreground=COLORS['text_primary'])
        
        self.style.configure('TFrame',
                            background=COLORS['bg_main'])
        
        self.style.configure('TEntry',
                            fieldbackground=COLORS['bg_input'],
                            foreground=COLORS['text_primary'],
                            borderwidth=1)
        
        self.style.configure('TLabel',
                            background=COLORS['bg_main'],
                            foreground=COLORS['text_primary'])
        
        self.style.configure('TNotebook',
                            background=COLORS['bg_main'],
                            borderwidth=0)
        self.style.configure('TNotebook.Tab',
                            background=COLORS['bg_secondary'],
                            foreground=COLORS['text_primary'],
                            padding=[10, 5])
        self.style.map('TNotebook.Tab',
                      background=[('selected', COLORS['bg_panel'])],
                      foreground=[('selected', COLORS['text_primary'])])
        
    def create_widgets(self):
        settings_frame = ttk.LabelFrame(self.root, text="Server Settings", padding=10)
        settings_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(settings_frame, text="Host:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.host_var = tk.StringVar(value="0.0.0.0")
        ttk.Entry(settings_frame, textvariable=self.host_var, width=15).grid(row=0, column=1, padx=5)
        
        ttk.Label(settings_frame, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.port_var = tk.StringVar(value="10000")
        ttk.Entry(settings_frame, textvariable=self.port_var, width=10).grid(row=0, column=3, padx=5)
        
        self.start_button = ttk.Button(settings_frame, text="Start Server", command=self.start_server)
        self.start_button.grid(row=0, column=4, padx=5)
        
        self.stop_button = ttk.Button(settings_frame, text="Stop Server", command=self.stop_server, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=5, padx=5)
        
        self.status_label = ttk.Label(settings_frame, text="Status: Stopped", foreground=COLORS['text_error'])
        self.status_label.grid(row=0, column=6, padx=10)
        
        stats_frame = ttk.LabelFrame(self.root, text="Statistics", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.stats_text = tk.Text(stats_frame, height=4, wrap=tk.WORD,
                                  bg=COLORS['bg_panel'], fg=COLORS['text_primary'],
                                  font=FONTS['default'], relief=tk.FLAT)
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        
        main_notebook = ttk.Notebook(self.root)
        main_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        visual_tab = ttk.Frame(main_notebook)
        main_notebook.add(visual_tab, text="Visual Network")
        self.create_visual_tab(visual_tab)
        
        table_tab = ttk.Frame(main_notebook)
        main_notebook.add(table_tab, text="Table View")
        
        clients_frame = ttk.LabelFrame(table_tab, text="Connected Clients", padding=10)
        clients_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ("Client ID", "Name", "Address", "Connected At", "Sent", "Received", "In Chat", "Groups")
        self.clients_tree = ttk.Treeview(clients_frame, columns=columns, show="headings", height=6)
        
        column_widths = {"Client ID": 120, "Name": 100, "Address": 130, "Connected At": 140, "Sent": 60, "Received": 60, "In Chat": 60, "Groups": 100}
        for col in columns:
            self.clients_tree.heading(col, text=col)
            self.clients_tree.column(col, width=column_widths.get(col, 150))
        
        scrollbar_clients = ttk.Scrollbar(clients_frame, orient=tk.VERTICAL, command=self.clients_tree.yview)
        self.clients_tree.configure(yscrollcommand=scrollbar_clients.set)
        
        self.clients_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_clients.pack(side=tk.RIGHT, fill=tk.Y)
        
        logs_frame = ttk.LabelFrame(table_tab, text="Server Logs", padding=10)
        logs_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.logs_text = scrolledtext.ScrolledText(logs_frame, height=10, wrap=tk.WORD,
                                                   bg=COLORS['list_bg'], fg=COLORS['text_primary'],
                                                   font=FONTS['monospace'], relief=tk.FLAT)
        self.logs_text.pack(fill=tk.BOTH, expand=True)
        
        buttons_frame = ttk.Frame(self.root)
        buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(buttons_frame, text="Clear Logs", command=self.clear_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Export Logs", command=self.export_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Export Statistics", command=self.export_statistics).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Refresh", command=self.update_all).pack(side=tk.LEFT, padx=5)
    
    def create_visual_tab(self, parent):
        """Create the visual network visualization tab."""
        left_frame = ttk.Frame(parent)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        canvas_frame = ttk.LabelFrame(left_frame, text="Network Visualization", padding=5)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.visual_canvas = tk.Canvas(canvas_frame, bg=COLORS['bg_secondary'], highlightthickness=0, 
                                       borderwidth=0, relief=tk.FLAT)
        scrollbar_v = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.visual_canvas.yview)
        scrollbar_h = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.visual_canvas.xview)
        self.visual_canvas.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        
        scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)
        self.visual_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.visual_canvas.bind("<Configure>", lambda e: self.update_visual_canvas_size())
        
        right_frame = ttk.Frame(parent)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)
        
        groups_frame = ttk.LabelFrame(right_frame, text="Groups", padding=5)
        groups_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        groups_list_frame = tk.Frame(groups_frame)
        groups_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar_groups = tk.Scrollbar(groups_list_frame)
        scrollbar_groups.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.groups_listbox = tk.Listbox(groups_list_frame, height=12, 
                                         yscrollcommand=scrollbar_groups.set,
                                         bg=COLORS['list_bg'], fg=COLORS['text_primary'], font=FONTS['default'],
                                         relief=tk.FLAT, selectbackground=COLORS['list_item_selected'])
        self.groups_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_groups.config(command=self.groups_listbox.yview)
        
        clients_info_frame = ttk.LabelFrame(right_frame, text="Clients Info", padding=5)
        clients_info_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        clients_list_frame = tk.Frame(clients_info_frame)
        clients_list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar_clients_info = tk.Scrollbar(clients_list_frame)
        scrollbar_clients_info.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.clients_info_listbox = tk.Listbox(clients_list_frame, height=12,
                                               yscrollcommand=scrollbar_clients_info.set,
                                               bg=COLORS['list_bg'], fg=COLORS['text_primary'], font=FONTS['default'],
                                               relief=tk.FLAT, selectbackground=COLORS['list_item_selected'])
        self.clients_info_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_clients_info.config(command=self.clients_info_listbox.yview)
        
        legend_frame = ttk.LabelFrame(right_frame, text="Legend", padding=5)
        legend_frame.pack(fill=tk.X, pady=5)
        
        legend_text = """Colors:
• Blue circles = Clients
• Green = In chat
• Orange lines = Chat connections
• Purple boxes = Groups
• Purple dashed = Group membership"""
        
        ttk.Label(legend_frame, text=legend_text, justify=tk.LEFT, font=FONTS['default']).pack(anchor=tk.W, padx=5, pady=5)
        
        self.update_visual_canvas_size()
        
    def update_visual_canvas_size(self):
        try:
            self.visual_canvas.update_idletasks()
            canvas_width = max(800, self.visual_canvas.winfo_width())
            canvas_height = max(600, self.visual_canvas.winfo_height())
            self.visual_canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))
        except:
            pass
        
    def log_message(self, message: str):
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.logs_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.logs_text.see(tk.END)
        
    def start_server(self):
        """Start the chat server."""
        if self.server_running:
            messagebox.showwarning("Warning", "Server is already running!")
            return
        
        try:
            host = self.host_var.get()
            port = int(self.port_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid port number!")
            return
        
        server_async.set_log_callback(self.log_message)
        
        self.server_running = True
        self.server_thread = threading.Thread(target=self.run_server, daemon=True)
        self.server_thread.start()
        
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="Status: Running", foreground=COLORS['status_online'])
        self.log_message(f"Server starting on {host}:{port}")
        
        self.update_statistics()
        
    def run_server(self):
        """Run server in async event loop."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            host = self.host_var.get()
            port = int(self.port_var.get())
            self.loop.run_until_complete(server_async.start_server(host=host, port=port))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self.log_message(f"Server error: {msg}"))
        finally:
            self.loop.close()
            
    def stop_server(self):
        """Stop the chat server."""
        if not self.server_running:
            return
        
        self.server_running = False
        
        try:
            import async_impl.server_async as server_async
            connected_clients = getattr(server_async, 'connected_clients', set())
            for writer in list(connected_clients):
                try:
                    if not writer.is_closing():
                        writer.close()
                except:
                    pass
        except:
            pass
        
        if self.loop and self.loop.is_running():
            try:
                tasks = [task for task in asyncio.all_tasks(self.loop) if not task.done()]
                for task in tasks:
                    task.cancel()
            except:
                pass
            self.loop.call_soon_threadsafe(self.loop.stop)
        
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Status: Stopped", foreground=COLORS['text_error'])
        self.log_message("Server stopped")
        
    def update_statistics(self):
        """Update server statistics display."""
        try:
            stats = server_async.get_statistics()
            
            self.stats_text.delete(1.0, tk.END)
            groups_count = len(stats.get('groups', {}))
            stats_str = f"""Connected Clients: {stats['connected_clients']}
Total Messages: {stats['total_messages']}
Messages Received: {stats['messages_received']}
Messages Sent: {stats['messages_sent']}
Active Groups: {groups_count}"""
            self.stats_text.insert(1.0, stats_str)
            
            self.clients_tree.delete(*self.clients_tree.get_children())
            for client_id, info in stats.get('clients_info', {}).items():
                groups_list = info.get('groups', [])
                groups_str = ", ".join(groups_list[:2])  # Show first 2 groups
                if len(groups_list) > 2:
                    groups_str += f" (+{len(groups_list) - 2})"
                if not groups_str:
                    groups_str = "-"
                self.clients_tree.insert("", tk.END, values=(
                    client_id,
                    info.get('name', 'Unknown'),
                    f"{info['address'][0]}:{info['address'][1]}",
                    info['connected_at'][:19],
                    info['messages_sent'],
                    info['messages_received'],
                    "Yes" if info.get('chat_partner', False) else "No",
                    groups_str
                ))
            
            self.clients = stats.get('clients_info', {})
            self.groups = stats.get('groups', {})
            
            self.draw_visual_network()
            
            self.groups_listbox.delete(0, tk.END)
            for group_name, members in self.groups.items():
                member_count = len(members)
                display = f"{group_name} ({member_count} members): {', '.join(members[:5])}"
                if len(members) > 5:
                    display += f" +{len(members) - 5} more"
                self.groups_listbox.insert(tk.END, display)
            
            self.clients_info_listbox.delete(0, tk.END)
            for client_id, info in self.clients.items():
                name = info.get('name', 'Unknown')
                chat_status = "In chat" if info.get('chat_partner') else "Available"
                groups_list = info.get('groups', [])
                groups_str = f"Groups: {', '.join(groups_list)}" if groups_list else "No groups"
                display = f"{name} - {chat_status} | {groups_str}"
                self.clients_info_listbox.insert(tk.END, display)
                
        except Exception as e:
            self.log_message(f"Error updating statistics: {e}")
        
        if self.server_running:
            self.root.after(2000, self.update_statistics)
        else:
            self.root.after(5000, self.update_statistics)
            
    def update_all(self):
        self.update_statistics()
        self.log_message("Manual refresh triggered")
        
    def clear_logs(self):
        self.logs_text.delete(1.0, tk.END)
        self.log_message("Logs cleared")
        
    def export_logs(self):
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if filename:
                server_async.export_logs(filename)
                self.log_message(f"Logs exported to {filename}")
                messagebox.showinfo("Success", f"Logs exported to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export logs: {e}")
            
    def export_statistics(self):
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if filename:
                stats = server_async.get_statistics()
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(stats, f, indent=2, ensure_ascii=False)
                self.log_message(f"Statistics exported to {filename}")
                messagebox.showinfo("Success", f"Statistics exported to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export statistics: {e}")
    
    def draw_visual_network(self):
        """Draw network visualization on canvas."""
        self.clear_visual_canvas()
        
        canvas_width = max(800, self.visual_canvas.winfo_width())
        canvas_height = max(600, self.visual_canvas.winfo_height())
        
        grid_color = COLORS['border_medium']
        for x in range(0, int(canvas_width), 50):
            self.visual_canvas.create_line(x, 0, x, canvas_height, fill=grid_color, width=1)
        for y in range(0, int(canvas_height), 50):
            self.visual_canvas.create_line(0, y, canvas_width, y, fill=grid_color, width=1)
        
        if not self.clients:
            center_x = canvas_width / 2
            center_y = canvas_height / 2
            self.visual_canvas.create_text(center_x, center_y - 30, 
                                         text="No clients connected", 
                                         fill=COLORS['text_muted'], font=FONTS['heading'], 
                                         justify=tk.CENTER)
            self.visual_canvas.create_text(center_x, center_y + 10, 
                                         text="Start the server and wait for connections", 
                                         fill=COLORS['text_secondary'], font=FONTS['medium'], 
                                         justify=tk.CENTER)
            return
        
        client_list = list(self.clients.items())
        center_x, center_y = 400, 300
        radius = min(200, 120 + len(client_list) * 12)
        
        client_positions = {}
        for i, (client_id, info) in enumerate(client_list):
            angle = (2 * math.pi * i) / len(client_list) - math.pi / 2
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            
            name = info.get('name', 'Unknown')
            has_chat = info.get('chat_partner', False)
            color = COLORS['accent_green'] if has_chat else COLORS['accent_primary']
            
            circle_id = self.visual_canvas.create_oval(x - 35, y - 35, x + 35, y + 35,
                                                      fill=color, outline=COLORS['border_light'], width=2)
            
            text_id = self.visual_canvas.create_text(x, y, text=name[:10], fill=COLORS['text_primary'],
                                                     font=FONTS['bold'])
            
            self.client_circles[client_id] = (circle_id, text_id, x, y)
            client_positions[client_id] = (x, y)
        
        client_by_name = {info.get('name'): cid for cid, info in self.clients.items()}
        drawn_connections = set()
        
        group_y_start = center_y + radius + 80
        group_x_start = 100
        group_spacing = 140
        
        for i, (group_name, members) in enumerate(self.groups.items()):
            x = group_x_start + (i % 5) * group_spacing
            y = group_y_start + (i // 5) * 70
            
            rect_id = self.visual_canvas.create_rectangle(x - 50, y - 18, x + 50, y + 18,
                                                         fill=COLORS['accent_secondary'], outline=COLORS['accent_primary'], width=2)
            
            text_id = self.visual_canvas.create_text(x, y, text=group_name[:10], fill=COLORS['text_primary'],
                                                     font=FONTS['small'])
            
            self.group_rects[group_name] = (rect_id, text_id, x, y)
            
            for member_name in members:
                if member_name in client_by_name:
                    member_id = client_by_name[member_name]
                    if member_id in client_positions:
                        mx, my = client_positions[member_id]
                        self.visual_canvas.create_line(x, y + 18, mx, my - 35, 
                                                      fill=COLORS['accent_secondary'], width=2, dash=(5, 3))
        
        stats = server_async.get_statistics()
        chat_connections = stats.get('chat_connections', {})
        client_by_name = {info.get('name'): cid for cid, info in self.clients.items()}
        
        drawn_connections = set()
        for client_id, partner_name in chat_connections.items():
            if client_id in client_positions and partner_name in client_by_name:
                partner_id = client_by_name[partner_name]
                if partner_id in client_positions:
                        connection_key = tuple(sorted([client_id, partner_id]))
                        if connection_key not in drawn_connections:
                            x1, y1 = client_positions[client_id]
                            x2, y2 = client_positions[partner_id]
                            line_id = self.visual_canvas.create_line(x1, y1, x2, y2, 
                                                                 fill=COLORS['text_warning'], width=3, tags='chat_connection')
                            self.visual_canvas.tag_lower(line_id)
                            self.connection_lines[connection_key] = line_id
                            drawn_connections.add(connection_key)
        
    def clear_visual_canvas(self):
        """Clear all visual elements from canvas."""
        self.visual_canvas.delete("all")
        self.client_circles = {}
        self.group_rects = {}
        self.connection_lines = {}


if __name__ == "__main__":
    root = tk.Tk()
    app = ServerGUI(root)
    root.mainloop()

