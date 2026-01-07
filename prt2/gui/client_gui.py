import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import asyncio
import threading
import csv
import time
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import async_impl.client_async as client_async

from gui.theme import COLORS, FONTS

try:
    from playsound import playsound
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False
    print("Warning: playsound not installed. Sound notifications will be disabled.")
    print("Install with: pip install playsound")

SOUND_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Icq old sound.mp3")

CONNECTION_TIMEOUT = 30.0
AUTO_REFRESH_INTERVAL_MS = 5000
GROUPS_LIST_DELAY_MS = 100
CHAT_OPEN_DELAY_MS = 50
GROUPS_UPDATE_DELAY_MS = 200
DEBOUNCE_DELAY_MS = 300


class ClientGUI:
    """Main GUI application for the chat client.
    
    Handles connection to server, user/group management, and chat interface.
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Client")
        self.root.configure(bg=COLORS['bg_main'])
        self.root.minsize(800, 600)
        self.root.resizable(True, True)
        
        self.connected = False
        self.sending_messages = False
        self.csv_file = None
        self.connection_reader = None
        self.connection_writer = None
        self.connection_loop = None
        self.client_name = ""
        
        self.chat_history = {}
        
        self.current_chat_target = None
        self.current_chat_is_group = False
        
        self.sound_enabled = True
        
        self.auto_refresh_enabled = True
        
        self.users = {}
        self.groups = {}
        self.my_groups = set()
        self.pending_group_selection = None
        

        self._refresh_pending = False
        self._groups_refresh_pending = False
        self._last_users_refresh = 0
        self._last_groups_refresh = 0
        self._refresh_debounce_timer = None
        self._groups_debounce_timer = None
        self._listbox_update_pending = False
        self._listbox_update_timer = None
        self._groups_listbox_update_pending = False
        self._groups_listbox_update_timer = None
        
        self.style = ttk.Style()
        self.configure_ttk_styles()
        
        self.create_widgets()
        

        self.root.update_idletasks()

        self.root.geometry("")
        self.root.update_idletasks()

        req_width = max(900, self.root.winfo_reqwidth() + 20)
        req_height = max(700, self.root.winfo_reqheight() + 20)
        self.root.geometry(f"{req_width}x{req_height}")
        self.root.update_idletasks()
        

        try:
            buttons_y = self.buttons_frame.winfo_y()
            window_height = self.root.winfo_height()
            buttons_height = self.buttons_frame.winfo_reqheight()
            if buttons_y + buttons_height > window_height:

                new_height = buttons_y + buttons_height + 50
                self.root.geometry(f"{req_width}x{new_height}")
                self.root.update_idletasks()
        except:
            pass
    
    def configure_ttk_styles(self):
        self.style.configure('Primary.TButton',
                            background=COLORS['btn_primary'],
                            foreground=COLORS['btn_text'],
                            borderwidth=0,
                            focuscolor='none',
                            relief=tk.FLAT,
                            padding=[15, 5])
        self.style.layout('Primary.TButton', [
            ('Button.button', {'children': [
                ('Button.focus', {'children': [
                    ('Button.padding', {'children': [
                        ('Button.label', {'side': 'left', 'expand': 1})
                    ]})
                ]})
            ]})
        ])
        self.style.map('Primary.TButton',
                      background=[('active', COLORS['btn_primary_hover']),
                                 ('pressed', COLORS['btn_primary_hover']),
                                 ('disabled', COLORS['btn_disabled'])],
                      foreground=[('active', COLORS['btn_text']),
                                 ('pressed', COLORS['btn_text'])],
                      bordercolor=[('focus', COLORS['btn_primary']),
                                  ('!focus', COLORS['btn_primary']),
                                  ('active', COLORS['btn_primary_hover']),
                                  ('pressed', COLORS['btn_primary_hover'])],
                      lightcolor=[('', COLORS['btn_primary']),
                                 ('active', COLORS['btn_primary_hover']),
                                 ('pressed', COLORS['btn_primary_hover'])],
                      darkcolor=[('', COLORS['btn_primary']),
                                ('active', COLORS['btn_primary_hover']),
                                 ('pressed', COLORS['btn_primary_hover'])])
        
        self.style.configure('Secondary.TButton',
                            background=COLORS['btn_secondary'],
                            foreground=COLORS['btn_text'],
                            borderwidth=0,
                            focuscolor='none',
                            relief=tk.FLAT,
                            padding=[10, 5])
        self.style.layout('Secondary.TButton', [
            ('Button.button', {'children': [
                ('Button.focus', {'children': [
                    ('Button.padding', {'children': [
                        ('Button.label', {'side': 'left', 'expand': 1})
                    ]})
                ]})
            ]})
        ])
        self.style.map('Secondary.TButton',
                      background=[('active', COLORS['btn_secondary_hover']),
                                 ('pressed', COLORS['btn_secondary_hover'])],
                      foreground=[('active', COLORS['btn_text']),
                                 ('pressed', COLORS['btn_text'])],
                      bordercolor=[('focus', COLORS['btn_secondary']),
                                  ('!focus', COLORS['btn_secondary']),
                                  ('active', COLORS['btn_secondary_hover']),
                                  ('pressed', COLORS['btn_secondary_hover'])],
                      lightcolor=[('', COLORS['btn_secondary']),
                                 ('active', COLORS['btn_secondary_hover']),
                                 ('pressed', COLORS['btn_secondary_hover'])],
                      darkcolor=[('', COLORS['btn_secondary']),
                                ('active', COLORS['btn_secondary_hover']),
                                ('pressed', COLORS['btn_secondary_hover'])])
        

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
        
        self.style.configure('Small.TButton',
                            background=COLORS['btn_secondary'],
                            foreground=COLORS['btn_text'],
                            borderwidth=0,
                            focuscolor='none',
                            relief=tk.FLAT,
                            padding=[5, 3])
        self.style.layout('Small.TButton', [
            ('Button.button', {'children': [
                ('Button.focus', {'children': [
                    ('Button.padding', {'children': [
                        ('Button.label', {'side': 'left', 'expand': 1})
                    ]})
                ]})
            ]})
        ])
        self.style.map('Small.TButton',
                      background=[('active', COLORS['btn_secondary_hover']),
                                 ('pressed', COLORS['btn_secondary_hover'])],
                      foreground=[('active', COLORS['btn_text']),
                                 ('pressed', COLORS['btn_text'])],
                      bordercolor=[('focus', COLORS['btn_secondary']),
                                  ('!focus', COLORS['btn_secondary']),
                                  ('active', COLORS['btn_secondary_hover']),
                                  ('pressed', COLORS['btn_secondary_hover'])],
                      lightcolor=[('', COLORS['btn_secondary']),
                                 ('active', COLORS['btn_secondary_hover']),
                                 ('pressed', COLORS['btn_secondary_hover'])],
                      darkcolor=[('', COLORS['btn_secondary']),
                                ('active', COLORS['btn_secondary_hover']),
                                 ('pressed', COLORS['btn_secondary_hover'])])
        
        self.style.configure('TLabelFrame',
                            background=COLORS['bg_main'],
                            foreground=COLORS['text_primary'],
                            borderwidth=0,
                            relief=tk.FLAT)
        self.style.configure('TLabelFrame.Label',
                            background=COLORS['bg_main'],
                            foreground=COLORS['text_primary'])
        
    def create_widgets(self):
        connection_frame = tk.Frame(self.root, bg=COLORS['bg_main'], pady=8)
        connection_frame.pack(fill=tk.X)
        
        left_conn = tk.Frame(connection_frame, bg=COLORS['bg_main'])
        left_conn.pack(side=tk.LEFT, padx=10)
        
        tk.Label(left_conn, text="Name:", bg=COLORS['bg_main'], fg=COLORS['text_primary'], font=FONTS['default']).pack(side=tk.LEFT, padx=5)
        self.name_var = tk.StringVar(value="")
        name_entry = tk.Entry(left_conn, textvariable=self.name_var, width=12, font=FONTS['default'],
                             bg=COLORS['list_bg'], fg=COLORS['text_primary'], relief=tk.FLAT, borderwidth=1,
                             highlightthickness=1, highlightbackground=COLORS['border_medium'], highlightcolor=COLORS['accent_primary'])
        name_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(left_conn, text="Host:", bg=COLORS['bg_main'], fg=COLORS['text_primary'], font=FONTS['default']).pack(side=tk.LEFT, padx=5)
        self.host_var = tk.StringVar(value="localhost")
        host_entry = tk.Entry(left_conn, textvariable=self.host_var, width=12, font=FONTS['default'],
                             bg=COLORS['list_bg'], fg=COLORS['text_primary'], relief=tk.FLAT, borderwidth=1,
                             highlightthickness=1, highlightbackground=COLORS['border_medium'], highlightcolor=COLORS['accent_primary'])
        host_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(left_conn, text="Port:", bg=COLORS['bg_main'], fg=COLORS['text_primary'], font=FONTS['default']).pack(side=tk.LEFT, padx=5)
        self.port_var = tk.StringVar(value="10000")
        port_entry = tk.Entry(left_conn, textvariable=self.port_var, width=8, font=FONTS['default'],
                             bg=COLORS['list_bg'], fg=COLORS['text_primary'], relief=tk.FLAT, borderwidth=1,
                             highlightthickness=1,                              highlightbackground=COLORS['border_medium'], highlightcolor=COLORS['accent_primary'])
        port_entry.pack(side=tk.LEFT, padx=5)
        
        right_conn = tk.Frame(connection_frame, bg=COLORS['bg_main'])
        right_conn.pack(side=tk.RIGHT, padx=10)
        
        self.connect_btn = ttk.Button(right_conn, text="Connect", command=self.connect,
                                      style='Primary.TButton')
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        self.disconnect_btn = ttk.Button(right_conn, text="Disconnect", command=self.disconnect,
                                         style='Primary.TButton', state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)
        
        self.status_label = tk.Label(right_conn, text="● Disconnected", bg=COLORS['bg_main'], fg=COLORS['text_muted'],
                                     font=FONTS['bold'])
        self.status_label.pack(side=tk.LEFT, padx=10)
        

        self.buttons_frame = tk.Frame(self.root, bg=COLORS['bg_main'], pady=5)
        
        main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=5, bg=COLORS['bg_main'])
        main_paned.pack(fill=tk.BOTH, expand=True)
        
        left_panel = tk.Frame(main_paned, bg=COLORS['bg_main'], width=250)
        main_paned.add(left_panel)
        
        users_frame = tk.LabelFrame(left_panel, text="Users", bg=COLORS['bg_main'], fg=COLORS['text_primary'],
                                   font=FONTS['bold'], padx=5, pady=5, relief=tk.FLAT, bd=0)
        users_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        users_list_frame = tk.Frame(users_frame, bg=COLORS['bg_main'])
        users_list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar_users = tk.Scrollbar(users_list_frame)
        scrollbar_users.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.users_listbox = tk.Listbox(users_list_frame, bg=COLORS['list_bg'], fg='#ffffff',
                                        font=FONTS['default'], relief=tk.FLAT,
                                        selectbackground=COLORS['list_item_selected'], selectforeground='#ffffff',
                                        yscrollcommand=scrollbar_users.set)
        self.users_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_users.config(command=self.users_listbox.yview)
        
        self.users_listbox.bind("<<ListboxSelect>>", lambda e: self.on_user_selected())
        
        users_btn_frame = tk.Frame(users_frame, bg=COLORS['bg_main'])
        users_btn_frame.pack(fill=tk.X, pady=5)
        chat_btn = ttk.Button(users_btn_frame, text="💬 Chat", command=self.open_chat_with_user,
                              style='Secondary.TButton')
        chat_btn.pack(fill=tk.X, pady=2)
        
        groups_frame = tk.LabelFrame(left_panel, text="Groups", bg=COLORS['bg_main'], fg=COLORS['text_primary'],
                                    font=FONTS['bold'], padx=5, pady=5, relief=tk.FLAT, bd=0)
        groups_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        create_group_frame = tk.Frame(groups_frame, bg=COLORS['bg_main'])
        create_group_frame.pack(fill=tk.X, pady=5)
        
        self.group_name_var = tk.StringVar(value="")
        group_entry = tk.Entry(create_group_frame, textvariable=self.group_name_var,
                              font=FONTS['small'], width=15, bg=COLORS['list_bg'], fg=COLORS['text_primary'],
                              relief=tk.FLAT, borderwidth=1, highlightthickness=1,
                              highlightbackground=COLORS['border_medium'], highlightcolor=COLORS['accent_primary'])
        group_entry.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        ttk.Button(create_group_frame, text="➕", command=self.create_group_visual,
                  style='Small.TButton', width=3).pack(side=tk.LEFT, padx=2)
        
        groups_list_frame = tk.Frame(groups_frame, bg=COLORS['bg_main'])
        groups_list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar_groups = tk.Scrollbar(groups_list_frame)
        scrollbar_groups.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.groups_listbox = tk.Listbox(groups_list_frame, bg=COLORS['bg_panel'], fg='#ffffff',
                                         font=FONTS['default'], relief=tk.FLAT,
                                         selectbackground=COLORS['list_item_selected'], selectforeground='#ffffff',
                                         yscrollcommand=scrollbar_groups.set)
        self.groups_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_groups.config(command=self.groups_listbox.yview)
        
        self.groups_listbox.bind("<<ListboxSelect>>", lambda e: self.on_group_selected())
        self.groups_listbox.bind("<Double-Button-1>", lambda e: self.open_group_chat())
        
        groups_btn_frame = tk.Frame(groups_frame, bg=COLORS['bg_main'])
        groups_btn_frame.pack(fill=tk.X, pady=5)
        
        btn_frame1 = tk.Frame(groups_btn_frame, bg=COLORS['bg_main'])
        btn_frame1.pack(fill=tk.X, pady=2)
        join_chat_btn = ttk.Button(btn_frame1, text="💬 Join & Chat", command=self.join_and_chat_group,
                                   style='Secondary.TButton')
        join_chat_btn.pack(fill=tk.X)
        
        btn_frame2 = tk.Frame(groups_btn_frame, bg=COLORS['bg_main'])
        btn_frame2.pack(fill=tk.X, pady=2)
        add_member_btn = ttk.Button(btn_frame2, text="➕ Add Member", command=self.add_member_to_group,
                                    style='Secondary.TButton')
        add_member_btn.pack(fill=tk.X)
        
        btn_frame3 = tk.Frame(groups_btn_frame, bg=COLORS['bg_main'])
        btn_frame3.pack(fill=tk.X, pady=2)
        leave_btn = ttk.Button(btn_frame3, text="➖ Leave", command=self.leave_group_from_list,
                               style='Secondary.TButton')
        leave_btn.pack(fill=tk.X)
        
        right_panel = tk.Frame(main_paned, bg=COLORS['bg_main'])
        main_paned.add(right_panel)
        
        main_frame = ttk.LabelFrame(right_panel, text="Chat", padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        chat_tab = tk.Frame(main_frame, bg=COLORS['bg_main'])
        chat_tab.pack(fill=tk.BOTH, expand=True)
        
        chat_header_frame = tk.Frame(chat_tab, bg=COLORS['chat_header_bg'], pady=10)
        chat_header_frame.pack(fill=tk.X)
        
        self.chat_title_label = tk.Label(chat_header_frame, text="Select a user to start chatting", 
                                         bg=COLORS['chat_header_bg'], fg=COLORS['text_primary'], 
                                         font=FONTS['title'])
        self.chat_title_label.pack()
        
        chat_content_frame = tk.Frame(chat_tab, bg=COLORS['chat_bg'])
        chat_content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.main_chat_text = scrolledtext.ScrolledText(chat_content_frame, wrap=tk.WORD, 
                                                        bg=COLORS['list_bg'], fg=COLORS['text_primary'], 
                                                        font=FONTS['medium'], relief=tk.FLAT, borderwidth=1,
                                                        insertbackground=COLORS['text_primary'])
        self.main_chat_text.pack(fill=tk.BOTH, expand=True)
        self.main_chat_text.config(state=tk.DISABLED)
        
        chat_input_frame = tk.Frame(chat_tab, bg=COLORS['chat_bg'], pady=5)
        chat_input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.main_message_entry = tk.Entry(chat_input_frame, font=FONTS['medium'], relief=tk.FLAT,
                                           bg=COLORS['bg_input'], fg=COLORS['text_primary'], borderwidth=1, 
                                           highlightthickness=1, highlightbackground=COLORS['border_medium'], 
                                           highlightcolor=COLORS['accent_primary'],
                                           insertbackground=COLORS['text_primary'], state=tk.DISABLED)
        self.main_message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.main_message_entry.bind("<Return>", lambda e: self.send_main_chat_message())
        
        self.main_send_btn = ttk.Button(chat_input_frame, text="Send", command=self.send_main_chat_message,
                                        style='Primary.TButton', state=tk.DISABLED)
        self.main_send_btn.pack(side=tk.LEFT, padx=5)
        

        self.buttons_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Button(self.buttons_frame, text="Clear Messages", command=self.clear_messages,
                  style='Secondary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(self.buttons_frame, text="Export Logs", command=self.export_logs,
                  style='Secondary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(self.buttons_frame, text="CSV Options", command=self.show_csv_menu,
                  style='Secondary.TButton').pack(side=tk.LEFT, padx=5)
        
    def show_csv_menu(self):
        csv_window = tk.Toplevel(self.root)
        csv_window.title("CSV File Options")
        csv_window.minsize(400, 200)
        csv_window.resizable(True, True)
        
        csv_frame = ttk.LabelFrame(csv_window, text="CSV File", padding=10)
        csv_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.csv_label = ttk.Label(csv_frame, text="No CSV file selected")
        self.csv_label.pack(pady=10)
        
        btn_frame = tk.Frame(csv_frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Browse CSV", command=self.browse_csv,
                  style='Secondary.TButton').pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="Send All Messages", command=self.send_all_messages,
                  style='Secondary.TButton').pack(side=tk.LEFT, padx=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(csv_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=10, padx=10)
        

        csv_window.update_idletasks()

        csv_window.geometry("")
        csv_window.update_idletasks()

        req_width = max(400, csv_window.winfo_reqwidth() + 20)
        req_height = max(200, csv_window.winfo_reqheight() + 20)
        csv_window.geometry(f"{req_width}x{req_height}")
        csv_window.update_idletasks()

    def browse_csv(self):
        filename = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.csv_file = filename
            if hasattr(self, 'csv_label'):
                self.csv_label.config(text=f"CSV: {filename.split('/')[-1]}")

    def connect(self):
        """Establish connection to the chat server.
        
        Connects to server, sends client name, and starts listening for messages.
        """
        if self.connected:
            return
        
        self.client_name = self.name_var.get().strip()
        if not self.client_name:
            messagebox.showwarning("Warning", "Please enter a name before connecting!")
            return
            
        try:
            host = self.host_var.get()
            port = int(self.port_var.get())
            
            client_async.HOST = host
            client_async.PORT = port
            
            def connect_async():
                try:
                    self.connection_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(self.connection_loop)
                    
                    async def do_connect():
                        self.connection_reader, self.connection_writer = await asyncio.open_connection(host, port)
                        try:
                            welcome_data = await asyncio.wait_for(self.connection_reader.read(4096), timeout=CONNECTION_TIMEOUT)
                        except asyncio.TimeoutError:
                            self.root.after(0, lambda: self._set_connected(False))
                            return
                        welcome = welcome_data.decode('utf-8').strip()
                        
                        name_with_newline = self.client_name + '\n'
                        self.connection_writer.write(name_with_newline.encode('utf-8'))
                        await self.connection_writer.drain()
                        
                        try:
                            name_response_data = await asyncio.wait_for(self.connection_reader.read(4096), timeout=CONNECTION_TIMEOUT)
                        except asyncio.TimeoutError:
                            self.root.after(0, lambda: self._set_connected(False))
                            return
                        name_response = name_response_data.decode('utf-8').strip()
                        
                        if "ERROR" in name_response:
                            self.root.after(0, lambda: messagebox.showerror("Error", name_response))
                            self.root.after(0, lambda: self._set_connected(False))
                            return
                        
                        self.root.after(0, lambda: self._set_connected(True))
                        self.root.after(0, lambda: self.refresh_users_visual())
                        self.root.after(GROUPS_LIST_DELAY_MS, lambda: self.list_groups_visual())
                        self.root.after(0, lambda: self.start_auto_refresh())
                        
                        async def read_messages():
                            buffer = ""
                            try:
                                while True:
                                    try:
                                        data = await self.connection_reader.read(4096)
                                    except Exception as e:
                                        break
                                    if not data:
                                        break
                                    buffer += data.decode('utf-8')

                                    while '\n' in buffer:
                                        line, buffer = buffer.split('\n', 1)
                                        message = line.strip()
                                        if message:

                                            if message != "LIST_USERS" and message != "LIST_GROUPS":
                                                self.root.after(0, lambda msg=message: self.handle_received_message(msg))
                            except Exception as e:
                                self.root.after(0, lambda: self._set_connected(False))
                        
                        asyncio.create_task(read_messages())
                        
                    self.connection_loop.run_until_complete(do_connect())
                    try:
                        self.connection_loop.run_forever()
                    except Exception:
                        pass
                except Exception as e:
                    error_msg = str(e)
                    self.root.after(0, lambda msg=error_msg: messagebox.showerror("Error", f"Connection failed: {msg}"))
                    self.root.after(0, lambda: self._set_connected(False))
            
            threading.Thread(target=connect_async, daemon=True).start()

        except Exception as e:
            messagebox.showerror("Error", f"Connection failed: {e}")

    def _set_connected(self, status: bool):
        self.connected = status
        if status:
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            self.status_label.config(text="● Connected", fg=COLORS['status_online'])
        else:
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
            self.status_label.config(text="● Disconnected", fg=COLORS['text_muted'])

    def disconnect(self):
        """Disconnect from the server and reset all connection state."""
        if self.connected and self.current_chat_target and not self.current_chat_is_group:
            self.send_command_safe("DISCONNECT_CHAT")
        
        if self.connection_writer and not self.connection_writer.is_closing():
            try:
                self.connection_writer.close()
            except:
                pass
        
        if self.connection_loop and self.connection_loop.is_running():
            try:
                tasks = [task for task in asyncio.all_tasks(self.connection_loop) if not task.done()]
                for task in tasks:
                    task.cancel()
                self.connection_loop.call_soon_threadsafe(self.connection_loop.stop)
            except:
                pass
        
        self.auto_refresh_enabled = False
        

        if self._refresh_debounce_timer:
            self.root.after_cancel(self._refresh_debounce_timer)
            self._refresh_debounce_timer = None
        if self._groups_debounce_timer:
            self.root.after_cancel(self._groups_debounce_timer)
            self._groups_debounce_timer = None
        if self._listbox_update_timer:
            self.root.after_cancel(self._listbox_update_timer)
            self._listbox_update_timer = None
        if self._groups_listbox_update_timer:
            self.root.after_cancel(self._groups_listbox_update_timer)
            self._groups_listbox_update_timer = None
        

        self._refresh_pending = False
        self._groups_refresh_pending = False
        self._listbox_update_pending = False
        self._groups_listbox_update_pending = False
        
        self._set_connected(False)
        self.connection_reader = None
        self.connection_writer = None
        self.connection_loop = None
        self.client_name = ""
        
        self.current_chat_target = None
        self.current_chat_is_group = False
        self.users = {}
        self.groups = {}
        self.my_groups = set()
        self.pending_group_selection = None
        
        self.chat_history = {}
        
        self.main_chat_text.config(state=tk.NORMAL)
        self.main_chat_text.delete(1.0, tk.END)
        self.main_chat_text.config(state=tk.DISABLED)
        self.main_message_entry.config(state=tk.DISABLED)
        self.main_send_btn.config(state=tk.DISABLED)
        self.chat_title_label.config(text="Select a user to start chatting")
        self._update_users_listbox_internal()
        self._update_groups_listbox_internal()
        
        self.auto_refresh_enabled = True

    def refresh_users_visual(self, force=False):
        """Request updated users list from server.
        
        Args:
            force: If True, bypass debouncing and refresh immediately
        """
        if not self.connected:
            return
        

        if not force and self._refresh_pending:
            return
        
        current_time = time.time()

        if not force and (current_time - self._last_users_refresh) < 0.5:
            self._refresh_pending = True
            if self._refresh_debounce_timer:
                self.root.after_cancel(self._refresh_debounce_timer)
            self._refresh_debounce_timer = self.root.after(DEBOUNCE_DELAY_MS, 
                lambda: self._do_refresh_users())
            return
        
        self._do_refresh_users()
    
    def _do_refresh_users(self):
        """Actually send LIST_USERS command."""
        if not self.connected:
            return
        
        self._refresh_pending = True
        self._last_users_refresh = time.time()
        

        self.send_command_safe("LIST_USERS")
        self._refresh_pending = False
    
    def start_auto_refresh(self):
        if not self.connected or not self.auto_refresh_enabled:
            return
        
        if not self.sending_messages:

            if not self._refresh_pending:
                self.refresh_users_visual()
            if not self._groups_refresh_pending:
                self.root.after(GROUPS_LIST_DELAY_MS, self.list_groups_visual)
        
        self.root.after(AUTO_REFRESH_INTERVAL_MS, self.start_auto_refresh)

    def list_groups_visual(self, force=False):
        """Request updated groups list from server.
        
        Args:
            force: If True, bypass debouncing and refresh immediately
        """
        if not self.connected:
            return
        

        if not force and self._groups_refresh_pending:
            return
        
        current_time = time.time()

        if not force and (current_time - self._last_groups_refresh) < 0.5:
            self._groups_refresh_pending = True
            if self._groups_debounce_timer:
                self.root.after_cancel(self._groups_debounce_timer)
            self._groups_debounce_timer = self.root.after(DEBOUNCE_DELAY_MS, 
                lambda: self._do_list_groups())
            return
        
        self._do_list_groups()
    
    def _do_list_groups(self):
        """Actually send LIST_GROUPS command."""
        if not self.connected:
            return
        
        self._groups_refresh_pending = True
        self._last_groups_refresh = time.time()
        

        self.send_command_safe("LIST_GROUPS")
        self._groups_refresh_pending = False

    async def send_command_async(self, command):
        """Send a command to the server asynchronously.
        
        Args:
            command: The command string to send (without newline)
        """
        try:
            if not self.connection_writer or self.connection_writer.is_closing():
                return
            message_with_newline = command + '\n'
            self.connection_writer.write(message_with_newline.encode('utf-8'))
            await self.connection_writer.drain()
        except Exception as e:

            pass
    
    def send_command_safe(self, command):
        """Thread-safe wrapper to send command to server.
        
        Args:
            command: The command string to send
        """
        if not self.connected or not self.connection_writer or self.connection_writer.is_closing():
            return
        
        try:
            asyncio.run_coroutine_threadsafe(
                self.send_command_async(command), self.connection_loop)
        except:
            pass

    def on_user_selected(self):
        selection = self.users_listbox.curselection()
        if not selection:
            return
        
        user_name = self.users_listbox.get(selection[0])
        self.show_chat_with_user(user_name, False)
    
    def show_chat_with_user(self, target_name, is_group):
        """Open and display chat with a user or group in the main chat interface.
        
        Args:
            target_name: Name of the user or group to chat with
            is_group: True if target is a group, False if it's a user
        """
        if not self.connected:
            return
        
        self.current_chat_target = target_name
        self.current_chat_is_group = is_group
        
        self._update_chat_title(target_name, is_group)
        
        self._update_chat_input_state(target_name, is_group)
        
        self._load_chat_history(target_name, is_group)
        
        if not is_group:
            self._establish_chat_connection(target_name)
        
        self.main_chat_text.config(state=tk.DISABLED)
        self.main_chat_text.see(tk.END)
    
    def _update_chat_title(self, target_name, is_group):
        if is_group:
            self.chat_title_label.config(text=f"{target_name} (Group Chat)")
        else:
            if target_name in self.users:
                self.chat_title_label.config(text=target_name)
            else:
                self.chat_title_label.config(text=f"{target_name} (Disconnected)")
    
    def _update_chat_input_state(self, target_name, is_group):
        if is_group:
            is_member = target_name in self.groups and self.client_name in self.groups[target_name]
            if is_member:
                self.main_message_entry.config(state=tk.NORMAL)
                self.main_send_btn.config(state=tk.NORMAL)
            else:
                self.main_message_entry.config(state=tk.DISABLED)
                self.main_send_btn.config(state=tk.DISABLED)
        else:
            is_connected = target_name in self.users
            if is_connected:
                self.main_message_entry.config(state=tk.NORMAL)
                self.main_send_btn.config(state=tk.NORMAL)
            else:
                self.main_message_entry.config(state=tk.DISABLED)
                self.main_send_btn.config(state=tk.DISABLED)
    
    def _load_chat_history(self, target_name, is_group):
        """Load and display chat history for the given target."""
        self.main_chat_text.config(state=tk.NORMAL)
        self.main_chat_text.delete(1.0, tk.END)
        
        chat_key = f"GROUP:{target_name}" if is_group else target_name
        
        if chat_key in self.chat_history and self.chat_history[chat_key]:
            for msg in self.chat_history[chat_key]:
                self.main_chat_text.insert(tk.END, msg + "\n")
        else:
            self.chat_history[chat_key] = []
            
            if is_group:
                self._show_group_welcome_message(target_name)
            else:
                self._show_direct_chat_welcome_message(target_name)
    
    def _show_group_welcome_message(self, group_name):
        if group_name in self.groups and self.client_name in self.groups[group_name]:
            members = self.groups[group_name]
            member_count = len(members)
            members_str = ", ".join(members[:5])
            if len(members) > 5:
                members_str += f" (+{len(members) - 5} more)"
            self.main_chat_text.insert(tk.END, 
                f"[System] Chatting in group: {group_name} ({member_count} members: {members_str})\n")
        else:
            self.main_chat_text.insert(tk.END, f"[System] Group: {group_name}\n")
    
    def _show_direct_chat_welcome_message(self, target_name):
        if target_name not in self.users:
            self.main_chat_text.insert(tk.END, f"[System] Connecting to {target_name}...\n")
    
    def _establish_chat_connection(self, target_name):
        """Send CONNECT command to establish chat connection with a user."""
        self.send_command_safe(f"CONNECT:{target_name}")
    
    def _update_chat_ui_for_disconnect(self):
        if self.current_chat_target and not self.current_chat_is_group:
            self.main_message_entry.config(state=tk.DISABLED)
            self.main_send_btn.config(state=tk.DISABLED)
            self.chat_title_label.config(text=f"{self.current_chat_target} (Disconnected)")
    
    def _update_chat_ui_for_connect(self):
        if self.current_chat_target and not self.current_chat_is_group:
            if self.current_chat_target in self.users:
                self.main_message_entry.config(state=tk.NORMAL)
                self.main_send_btn.config(state=tk.NORMAL)
                self.chat_title_label.config(text=self.current_chat_target)
    
    def _update_chat_ui_for_group_membership(self):
        if self.current_chat_target and self.current_chat_is_group:
            is_member = (self.current_chat_target in self.groups and 
                        self.client_name in self.groups[self.current_chat_target])
            
            if is_member:
                self.main_message_entry.config(state=tk.NORMAL)
                self.main_send_btn.config(state=tk.NORMAL)
            else:
                self.main_message_entry.config(state=tk.DISABLED)
                self.main_send_btn.config(state=tk.DISABLED)
    
    def _close_chat_after_disconnect(self):
        """Close chat interface when user disconnects."""
        if not (self.current_chat_target and not self.current_chat_is_group):
            return
        
        if self.current_chat_target in self.users:
            return
        
        if self.connected:
            self.send_command_safe("DISCONNECT_CHAT")
        
        self.current_chat_target = None
        self.current_chat_is_group = False
        
        self.main_chat_text.config(state=tk.NORMAL)
        self.main_chat_text.delete(1.0, tk.END)
        self.main_chat_text.config(state=tk.DISABLED)
        
        self.main_message_entry.config(state=tk.DISABLED)
        self.main_send_btn.config(state=tk.DISABLED)
        self.chat_title_label.config(text="Select a user to start chatting")
    
    def send_main_chat_message(self):
        """Send message from the main chat input field."""
        if not self.current_chat_target or not self.connected:
            return
        
        if not self.current_chat_is_group:
            if self.current_chat_target not in self.users:
                return
        else:
            if self.current_chat_target not in self.groups or self.client_name not in self.groups[self.current_chat_target]:
                return
        
        message = self.main_message_entry.get().strip()
        if not message:
            return
        
        if message == "LIST_USERS" or message == "LIST_GROUPS":
            self.main_message_entry.delete(0, tk.END)
            return
        
        self.main_message_entry.delete(0, tk.END)
        
        self.send_chat_message(self.current_chat_target, message, self.current_chat_is_group)
    
    def play_notification_sound(self):
        if not self.sound_enabled or not SOUND_AVAILABLE:
            return
        
        if not os.path.exists(SOUND_FILE):
            return
        
        def play_sound():
            try:
                playsound(SOUND_FILE, block=False)
            except Exception as e:
                print(f"Error playing sound: {e}")
        
        threading.Thread(target=play_sound, daemon=True).start()
    
    def add_message_to_main_chat(self, sender, message, is_me=False):
        """Add a message to the main chat display and save to history.
        
        Args:
            sender: Name of the message sender (None for system messages)
            message: Message text
            is_me: True if message is from current user
        """
        if not self.current_chat_target:
            return
        
        self.main_chat_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime('%H:%M')
        if is_me:
            display_msg = f"[{timestamp}] You: {message}"
        else:
            if sender:
                display_msg = f"[{timestamp}] {sender}: {message}"
            else:
                display_msg = f"[{timestamp}] {message}"
        
        self.main_chat_text.insert(tk.END, display_msg + "\n")
        self.main_chat_text.config(state=tk.DISABLED)
        self.main_chat_text.see(tk.END)
        
        if not is_me:
            self.play_notification_sound()
        
        chat_key = f"GROUP:{self.current_chat_target}" if self.current_chat_is_group else self.current_chat_target
        if chat_key not in self.chat_history:
            self.chat_history[chat_key] = []
        self.chat_history[chat_key].append(display_msg)
    
    def open_chat_with_user(self):
        selection = self.users_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user!")
            return
        
        user_name = self.users_listbox.get(selection[0])
        self.show_chat_with_user(user_name, False)

    def on_group_selected(self):
        selection = self.groups_listbox.curselection()
        if not selection:
            return
        
        group_name = self.groups_listbox.get(selection[0]).split(" (")[0]
        self.show_chat_with_user(group_name, True)
    
    def open_group_chat(self):
        selection = self.groups_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a group!")
            return
        
        group_name = self.groups_listbox.get(selection[0]).split(" (")[0]
        self.show_chat_with_user(group_name, True)
    
    def add_member_to_group(self):
        selection = self.groups_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a group!")
            return
        
        group_name = self.groups_listbox.get(selection[0]).split(" (")[0]
        
        if group_name not in self.groups or self.client_name not in self.groups[group_name]:
            messagebox.showwarning("Warning", "You must be a member of the group to add members!")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Add Member to {group_name}")
        dialog.configure(bg=COLORS['bg_main'])
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.minsize(300, 400)
        dialog.resizable(True, True)
        
        tk.Label(dialog, text=f"Select a user to add to '{group_name}':", 
                bg=COLORS['bg_main'], fg=COLORS['text_primary'], font=FONTS['bold']).pack(pady=10)
        
        list_frame = tk.Frame(dialog, bg=COLORS['bg_main'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        users_listbox = tk.Listbox(list_frame, bg=COLORS['list_bg'], fg='#ffffff',
                                   font=FONTS['default'], relief=tk.FLAT,
                                   selectbackground=COLORS['list_item_selected'], 
                                   selectforeground='#ffffff',
                                   yscrollcommand=scrollbar.set)
        users_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=users_listbox.yview)
        
        current_members = set(self.groups.get(group_name, []))
        
        available_users = []
        for user_name in sorted(self.users.keys()):
            if user_name != self.client_name and user_name not in current_members:
                users_listbox.insert(tk.END, user_name)
                available_users.append(user_name)
        
        if not available_users:
            users_listbox.insert(tk.END, "(No users available to add)")
            users_listbox.config(state=tk.DISABLED)
        
        btn_frame = tk.Frame(dialog, bg=COLORS['bg_main'])
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def do_add():
            selection = users_listbox.curselection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a user!")
                return
            
            user_name = users_listbox.get(selection[0])
            if user_name == "(No users available to add)":
                return
            
            self.send_command_safe(f"INVITE_TO_GROUP:{group_name}:{user_name}")
            dialog.destroy()
        
        ttk.Button(btn_frame, text="Add", command=do_add, 
                  style='Primary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, 
                  style='Secondary.TButton').pack(side=tk.LEFT, padx=5)
        

        dialog.update_idletasks()

        dialog.geometry("")
        dialog.update_idletasks()

        req_width = max(300, dialog.winfo_reqwidth() + 20)
        req_height = max(400, dialog.winfo_reqheight() + 20)
        dialog.geometry(f"{req_width}x{req_height}")
        dialog.update_idletasks()

    def join_and_chat_group(self):
        """Join selected group and open chat with it."""
        selection = self.groups_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a group!")
            return
        
        group_name = self.groups_listbox.get(selection[0]).split(" (")[0]
        
        if group_name not in self.groups:
            self.groups[group_name] = [self.client_name]
        elif self.client_name not in self.groups[group_name]:
            self.groups[group_name].append(self.client_name)
        
        self.pending_group_selection = group_name
        
        self.update_groups_listbox()
        
        self.send_command_safe(f"JOIN_GROUP:{group_name}")
        self.show_chat_with_user(group_name, True)

    def create_group_visual(self):
        """Create a new group with the name from input field."""
        group_name = self.group_name_var.get().strip()
        if not group_name:
            messagebox.showwarning("Warning", "Please enter a group name in the text field above!")
            return
        
        if not self.connected:
            messagebox.showwarning("Warning", "Please connect first!")
            return
        
        self.send_command_safe(f"CREATE_GROUP:{group_name}")
        self.group_name_var.set("")

    def leave_group_from_list(self):
        """Leave the selected group."""
        selection = self.groups_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a group!")
            return
        
        group_name = self.groups_listbox.get(selection[0]).split(" (")[0]
        
        self.send_command_safe(f"LEAVE_GROUP:{group_name}")
        
        if self.current_chat_target == group_name and self.current_chat_is_group:
            self.current_chat_target = None
            self.current_chat_is_group = False
            self.main_chat_text.config(state=tk.NORMAL)
            self.main_chat_text.delete(1.0, tk.END)
            self.main_chat_text.config(state=tk.DISABLED)
            self.main_message_entry.config(state=tk.DISABLED)
            self.main_send_btn.config(state=tk.DISABLED)
            self.chat_title_label.config(text="Select a user to start chatting")

    def send_chat_message(self, target, message, is_group):
        """Send a chat message to a user or group.
        
        Args:
            target: Name of user or group to send message to
            message: Message text to send
            is_group: True if target is a group, False if it's a user
        """
        if not self.connected:
            return
        
        if not is_group:
            if target not in self.users:
                return
        
        if is_group:
            command = f"GROUP:{target}:{message}"
        else:
            command = message
        
        self.send_command_safe(command)

        if self.current_chat_target == target and self.current_chat_is_group == is_group:
            self.add_message_to_main_chat("You", message, is_me=True)
        else:
            chat_key = f"GROUP:{target}" if is_group else target
            if chat_key not in self.chat_history:
                self.chat_history[chat_key] = []
            timestamp = datetime.now().strftime('%H:%M')
            self.chat_history[chat_key].append(f"[{timestamp}] You: {message}")

    def handle_received_message(self, message):
        """Process incoming message from server.
        
        Handles various message types: user connections, group updates, chat messages, errors.
        
        Args:
            message: The raw message string from server
        """
        msg_stripped = message.strip()
        if msg_stripped == "LIST_USERS" or msg_stripped == "LIST_GROUPS":
            return
        
        if message.startswith("USER_CONNECTED:"):
            try:
                new_user_name = message.split(":", 1)[1].strip()
                if new_user_name and new_user_name != self.client_name:
                    if self.current_chat_target == new_user_name and not self.current_chat_is_group:
                        self.add_message_to_main_chat("System", f"{new_user_name} is now online")
                        self._update_chat_ui_for_connect()
                        self._establish_chat_connection(new_user_name)
                    
                    self.root.after(GROUPS_LIST_DELAY_MS, lambda: self.refresh_users_visual(force=True))
                return
            except:
                pass
        if "Connected users" in message or message.startswith("Connected users"):
            try:
                parts = message.split(":", 1)
                if len(parts) > 1:
                    users_str = parts[1].strip()

                    if "(" in users_str:

                        users_str = users_str.split(")", 1)[1].strip()
                        if users_str.startswith(":"):
                            users_str = users_str[1:].strip()
                    user_list = [u.strip() for u in users_str.split(",") if u.strip()]
                    if user_list or not self.users:
                        self.update_users_display(user_list)
                    return
            except Exception as e:

                print(f"Error parsing users list: {e}")
                pass
            return
        elif "Available groups" in message or message.startswith("Available groups") or message.startswith("No groups available"):
            try:
                if message.startswith("No groups available"):
                    self.groups = {}
                    self.update_groups_listbox()
                    return
                
                lines = message.split("\n")
                groups_dict = {}
                for line in lines:
                    if "(" in line and "members" in line:
                        group_name = line.split("(")[0].strip()
                        if group_name:
                            if "members:" in line:
                                members_str = line.split("members:")[1].split(")")[0].strip()
                                members = [m.strip() for m in members_str.split(",") if m.strip()]
                                groups_dict[group_name] = members
                            else:
                                groups_dict[group_name] = []
                
                old_groups = dict(self.groups)
                
                preserved_groups = {}
                if self.pending_group_selection:
                    if self.pending_group_selection not in groups_dict:
                        if self.pending_group_selection in old_groups:
                            if self.client_name in old_groups[self.pending_group_selection]:
                                preserved_groups[self.pending_group_selection] = old_groups[self.pending_group_selection]
                        else:
                            if self.pending_group_selection in self.groups and self.client_name in self.groups[self.pending_group_selection]:
                                preserved_groups[self.pending_group_selection] = self.groups[self.pending_group_selection]
                
                for group_name, members in old_groups.items():
                    if group_name not in groups_dict and self.client_name in members:
                        preserved_groups[group_name] = members
                
                self.groups = groups_dict.copy()
                
                for group_name, members in preserved_groups.items():
                    self.groups[group_name] = members
                
                if self.pending_group_selection and self.pending_group_selection in groups_dict:
                    pass
                
                self.update_groups_listbox()
                if self.current_chat_target and self.current_chat_is_group:
                    was_member = self.current_chat_target in old_groups and self.client_name in old_groups.get(self.current_chat_target, [])
                    is_member = self.current_chat_target in self.groups and self.client_name in self.groups.get(self.current_chat_target, [])
                    if was_member != is_member:
                        self._update_chat_ui_for_group_membership()
                return
            except Exception as e:
                print(f"Error parsing groups: {e}")
                pass
            return
        elif "Group" in message and ("created" in message.lower() or "You are now a member" in message):
            try:
                if "'" in message:
                    group_name = message.split("'")[1]
                    if group_name not in self.groups:
                        self.groups[group_name] = [self.client_name]
                    elif self.client_name not in self.groups[group_name]:
                        self.groups[group_name].append(self.client_name)
                    self.pending_group_selection = group_name
                    self.update_groups_listbox()
                    self.root.after(CHAT_OPEN_DELAY_MS, lambda: self.show_chat_with_user(group_name, True))
                    if self.current_chat_target == group_name and self.current_chat_is_group:
                        self.add_message_to_main_chat("System", message.strip())
            except:
                pass

            if not self._groups_refresh_pending:
                self.root.after(GROUPS_UPDATE_DELAY_MS, self.list_groups_visual)
            return
        elif "was added to group" in message.lower() or "you were added to group" in message.lower():
            if "you were added to group" in message.lower():
                try:
                    if "'" in message:
                        group_name = message.split("'")[1]
                        if group_name not in self.groups:
                            self.groups[group_name] = [self.client_name]
                        elif self.client_name not in self.groups[group_name]:
                            self.groups[group_name].append(self.client_name)
                        self.pending_group_selection = group_name
                        self.update_groups_listbox()
                        if self.current_chat_target == group_name and self.current_chat_is_group:
                            self.add_message_to_main_chat("System", message.strip())
                        self._update_chat_ui_for_group_membership()
                except:
                    pass

            if not self._groups_refresh_pending:
                self.root.after(100, self.list_groups_visual)
            return
        elif "has disconnected" in message.lower() and ("you can no longer send messages" in message.lower() or "[System]" in message):
            try:
                disconnected_name = None
                if "[System]" in message:
                    parts = message.split("[System]")[1].strip()
                    if " has disconnected" in parts:
                        disconnected_name = parts.split(" has disconnected")[0].strip()
                
                if self.current_chat_target and not self.current_chat_is_group:
                    if disconnected_name:
                        self.add_message_to_main_chat("System", f"{disconnected_name} has been disconnected")
                    else:
                        self.add_message_to_main_chat("System", f"{self.current_chat_target} has been disconnected")
                    self._close_chat_after_disconnect()
                
                if disconnected_name and disconnected_name in self.users:
                    del self.users[disconnected_name]
                    self.update_users_listbox()
            except Exception as e:
                print(f"Error handling disconnect message: {e}")
            return
        elif "joined group" in message.lower() or "left group" in message.lower():

            if not self._groups_refresh_pending:
                self.root.after(GROUPS_UPDATE_DELAY_MS, self.list_groups_visual)
            return
        elif "GROUP_UPDATED" in message:

            if not self._groups_refresh_pending:
                self.root.after(100, self.list_groups_visual)
            return
        elif message.startswith("[") and "]" in message:
            try:
                closing_bracket_pos = message.find("]")
                if closing_bracket_pos == -1:
                    return
                
                message_source = message[1:closing_bracket_pos].strip()
                if not message_source:
                    return
                
                message_body = message[closing_bracket_pos + 1:].strip()
                if not message_body:
                    return
                
                if message_body.startswith(":"):
                    message_body = message_body[1:].strip()
                
                if not message_body:
                    return
                
                if message_body == "LIST_USERS" or message_body == "LIST_GROUPS":
                    return
                
                colon_pos = message_body.find(":")
                if colon_pos != -1:
                    sender = message_body[:colon_pos].strip()
                    msg_content = message_body[colon_pos + 1:].strip()
                    
                    if not sender or not msg_content:
                        return
                    
                    if message_source in self.groups:
                        group_key = f"GROUP:{message_source}"
                        
                        if self.current_chat_target == message_source and self.current_chat_is_group:
                            self.add_message_to_main_chat(sender, msg_content)
                        else:
                            self.play_notification_sound()
                        
                        if group_key not in self.chat_history:
                            self.chat_history[group_key] = []
                        timestamp = datetime.now().strftime('%H:%M')
                        self.chat_history[group_key].append(f"[{timestamp}] {sender}: {msg_content}")
                        
                        return
                    else:
                        sender_name = message_source
                        msg_content = message_body.strip()
                        
                        if self.current_chat_target == sender_name and not self.current_chat_is_group:
                            self.add_message_to_main_chat(sender_name, msg_content)
                        else:
                            self.play_notification_sound()
                        
                        if sender_name not in self.chat_history:
                            self.chat_history[sender_name] = []
                        timestamp = datetime.now().strftime('%H:%M')
                        self.chat_history[sender_name].append(f"[{timestamp}] {sender_name}: {msg_content}")
                        
                        return
                else:
                    sender = message_source
                    msg_content = message_body.strip()
                    
                    if not msg_content:
                        return
                    
                    if self.current_chat_target == sender and not self.current_chat_is_group:
                        self.add_message_to_main_chat(sender, msg_content)
                    else:
                        self.play_notification_sound()
                    
                    if sender not in self.chat_history:
                        self.chat_history[sender] = []
                    timestamp = datetime.now().strftime('%H:%M')
                    self.chat_history[sender].append(f"[{timestamp}] {sender}: {msg_content}")
                    
                    return
                    
            except Exception as e:
                print(f"Error parsing chat message: {e}, message: {message}")
                return
        elif "ERROR" in message and "Group" in message and "already exists" in message.lower():
            messagebox.showerror("Error", message.strip())
            return
        elif "ERROR" in message and "already connected" in message.lower():
            try:
                if "'" in message:
                    target_name = message.split("'")[1].split("'")[0]
                    if target_name and self.current_chat_target == target_name and not self.current_chat_is_group:
                        self._update_chat_ui_for_connect()
            except:
                pass
            return
        elif "ERROR" in message and ("disconnected" in message.lower() or "Message delivery failed" in message or "Chat partner has disconnected" in message):
            if self.current_chat_target and not self.current_chat_is_group:
                self.add_message_to_main_chat("System", f"{self.current_chat_target} has been disconnected")
                self._close_chat_after_disconnect()
            return
        elif "connected to you" in message.lower() and "you can now send messages directly" in message.lower():
            try:
                idx = message.lower().find(" connected to you")
                if idx > 0:
                    sender_name = message[:idx].strip()
                    if sender_name and sender_name != self.client_name:
                        if sender_name not in self.users:
                            self.users[sender_name] = {'name': sender_name}
                            self.update_users_listbox()
                        if not self.current_chat_target:
                            self.show_chat_with_user(sender_name, False)
                        elif self.current_chat_target == sender_name and not self.current_chat_is_group:
                            was_disconnected = (self.main_message_entry['state'] == 'disabled' or 
                                              self.chat_title_label.cget('text').endswith('(Disconnected)'))
                            if was_disconnected:
                                self.add_message_to_main_chat("System", f"{sender_name} is now online")
                            else:
                                self.add_message_to_main_chat("System", f"{sender_name} connected to you. You can now chat!")
                            self._update_chat_ui_for_connect()
            except Exception as e:
                pass
            return
        elif message.startswith("Connected to ") and "You can now send messages directly" in message:
            try:
                if "Connected to " in message and "." in message:
                    target_name = message.split("Connected to ")[1].split(".")[0].strip()
                    if target_name and target_name != self.client_name:
                        if target_name not in self.users:
                            self.users[target_name] = {'name': target_name}
                            self.update_users_listbox()
                        if self.current_chat_target == target_name and not self.current_chat_is_group:
                            was_disconnected = (self.main_message_entry['state'] == 'disabled' or 
                                              self.chat_title_label.cget('text').endswith('(Disconnected)'))
                            if was_disconnected:
                                self.add_message_to_main_chat("System", f"{target_name} is now online")
                            else:
                                self.add_message_to_main_chat("System", f"Connected to {target_name}. You can now chat!")
                            self._update_chat_ui_for_connect()
            except Exception as e:
                pass
            return
        elif "joined group" in message.lower() or "left group" in message.lower() or "created" in message.lower() or "connected to" in message.lower():
            if ("joined" in message.lower() or "created" in message.lower()) and not self._groups_refresh_pending:
                self.list_groups_visual()
            return

    def update_users_display(self, user_list):
        """Update the users display with new list from server.
        
        Args:
            user_list: List of user names currently connected
        """
        def _update():
            selected = self.users_listbox.curselection()
            selected_name = None
            if selected:
                try:
                    selected_name = self.users_listbox.get(selected[0])
                except:
                    pass
            
            new_users = {name: {'name': name} for name in user_list if name != self.client_name}
            
            if new_users or not user_list:
                old_users = set(self.users.keys())
                self.users = new_users
                self._update_users_listbox_internal()
                
                if selected_name and selected_name in self.users:
                    try:
                        index = sorted(self.users.keys()).index(selected_name)
                        self.users_listbox.selection_set(index)
                        self.users_listbox.see(index)
                    except:
                        pass
                
                if self.current_chat_target and not self.current_chat_is_group:
                    if self.current_chat_target not in self.users and self.current_chat_target in old_users:
                        self.add_message_to_main_chat("System", f"{self.current_chat_target} has been disconnected")
                        self._update_chat_ui_for_disconnect()
                        self._close_chat_after_disconnect()
                    elif self.current_chat_target in self.users:
                        if (self.main_message_entry['state'] == 'disabled' or 
                            self.chat_title_label.cget('text').endswith('(Disconnected)')):
                            self.add_message_to_main_chat("System", f"{self.current_chat_target} is now online")
                            self._update_chat_ui_for_connect()
                            self._establish_chat_connection(self.current_chat_target)
        
        self.root.after(0, _update)

    def update_users_listbox(self):
        """Update users listbox with debouncing to prevent excessive updates."""
        if self._listbox_update_pending:
            return
        
        self._listbox_update_pending = True
        if self._listbox_update_timer:
            self.root.after_cancel(self._listbox_update_timer)
        self._listbox_update_timer = self.root.after(50, self._update_users_listbox_debounced)
    
    def _update_users_listbox_debounced(self):
        """Actually update the users listbox after debounce."""
        self._listbox_update_pending = False
        self._listbox_update_timer = None
        self._update_users_listbox_internal()
    
    def _update_users_listbox_internal(self):
        self.users_listbox.delete(0, tk.END)
        if self.users:
            for name in sorted(self.users.keys()):
                self.users_listbox.insert(tk.END, name)
        else:
            if self.connected:
                self.users_listbox.insert(tk.END, "(No other users connected)")

    def update_groups_listbox(self):
        """Update groups listbox with debouncing to prevent excessive updates."""
        if self._groups_listbox_update_pending:
            return
        
        self._groups_listbox_update_pending = True
        if self._groups_listbox_update_timer:
            self.root.after_cancel(self._groups_listbox_update_timer)
        self._groups_listbox_update_timer = self.root.after(50, self._update_groups_listbox_debounced)
    
    def _update_groups_listbox_debounced(self):
        """Actually update the groups listbox after debounce."""
        self._groups_listbox_update_pending = False
        self._groups_listbox_update_timer = None
        self._update_groups_listbox_internal()
    
    def _update_groups_listbox_internal(self):
        selection = self.groups_listbox.curselection()
        selected_group = None
        if selection:
            try:
                selected_group = self.groups_listbox.get(selection[0]).split(" (")[0]
            except:
                pass
        
        if self.pending_group_selection:
            selected_group = self.pending_group_selection
        
        self.groups_listbox.delete(0, tk.END)
        
        if self.groups:
            sorted_groups = sorted(self.groups.keys())
            for group_name in sorted_groups:
                members = self.groups[group_name]
                member_count = len(members)
                display = f"{group_name} ({member_count} members)"
                self.groups_listbox.insert(tk.END, display)
            
            if selected_group and selected_group in self.groups:
                try:
                    index = sorted_groups.index(selected_group)
                    self.groups_listbox.selection_set(index)
                    self.groups_listbox.see(index)
                    if self.pending_group_selection == selected_group:
                        self.pending_group_selection = None
                except:
                    pass
        
        my_groups = {}
        for group_name, members in self.groups.items():
            if self.client_name in members:
                my_groups[group_name] = members
        self.my_groups = set(my_groups.keys())
        
        if self.current_chat_target and self.current_chat_is_group:
            self._update_chat_ui_for_group_membership()

    def send_all_messages(self):
        """Send all messages from the selected CSV file to the server."""
        if not self.connected:
            messagebox.showwarning("Warning", "Please connect first!")
            return
        
        if not self.csv_file:
            messagebox.showwarning("Warning", "Please select a CSV file first!")
            return
        
        if self.sending_messages:
            messagebox.showwarning("Warning", "Already sending messages!")
            return

        threading.Thread(target=self._send_all_async, daemon=True).start()

    def _send_all_async(self):
        try:
            self.sending_messages = True
            
            client_async.HOST = self.host_var.get()
            client_async.PORT = int(self.port_var.get())
            
            total_messages = 0
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['src_app'] == 'client_browser' and row['dst_app'] == 'web_server':
                        total_messages += 1
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(client_async.send_messages_from_csv(self.csv_file, delay=0.1))
            finally:
                try:
                    pending = asyncio.all_tasks(loop)
                    for task in pending:
                        task.cancel()
                    if pending:
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                except:
                    pass
                loop.close()
            
            self.root.after(0, lambda: self.progress_var.set(100))
            
        except Exception as e:
            pass
        finally:
            self.sending_messages = False

    def clear_messages(self):
        if self.current_chat_target:
            self.main_chat_text.config(state=tk.NORMAL)
            self.main_chat_text.delete(1.0, tk.END)
            self.main_chat_text.config(state=tk.DISABLED)
            chat_key = f"GROUP:{self.current_chat_target}" if self.current_chat_is_group else self.current_chat_target
            if chat_key in self.chat_history:
                self.chat_history[chat_key] = []

    def export_logs(self):
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if filename:
                client_async.export_logs(filename)
                messagebox.showinfo("Success", f"Logs exported to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export logs: {e}")



if __name__ == "__main__":
    root = tk.Tk()
    app = ClientGUI(root)
    root.mainloop()
