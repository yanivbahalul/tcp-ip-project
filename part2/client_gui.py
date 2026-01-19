import tkinter as tk
from tkinter import messagebox
import random
import os
from PIL import Image, ImageTk
from client import ChatLogic

# --- CONFIG & ASSETS ---

class Marquee(tk.Canvas):
    def __init__(self, parent, quotes, bg, fg):
        super().__init__(parent, bg=bg, height=30, highlightthickness=0)
        self.quotes = quotes
        self.current_quote_idx = 0
        self.fg = fg
        self.width = 800
        self.text_obj = self.create_text(0, 15, text=self.quotes[self.current_quote_idx], fill=fg, font=("Comic Sans MS", 12, "bold"), anchor='w')
        self.x_pos = 0
        self.change_timer = 0
        self.animate()

    def animate(self):
        self.move(self.text_obj, -2, 0)
        self.x_pos -= 2
        self.change_timer += 1
        
        bbox = self.bbox(self.text_obj)
        if bbox[2] < 0:
            self.current_quote_idx = (self.current_quote_idx + 1) % len(self.quotes)
            self.delete(self.text_obj)
            self.text_obj = self.create_text(self.width, 15, text=self.quotes[self.current_quote_idx], fill=self.fg, font=("Comic Sans MS", 12, "bold"), anchor='w')
            self.x_pos = self.width
        
        if self.change_timer >= 1500:
            self.current_quote_idx = (self.current_quote_idx + 1) % len(self.quotes)
            self.delete(self.text_obj)
            self.text_obj = self.create_text(self.width, 15, text=self.quotes[self.current_quote_idx], fill=self.fg, font=("Comic Sans MS", 12, "bold"), anchor='w')
            self.x_pos = self.width
            self.change_timer = 0
        
        self.after(50, self.animate)

class Y2KPinkPaletteGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ONLINE CHAT")
        self.root.geometry("600x550")

        self.palette = {
            "dark_grey":  "#2C2C2C",
            "dark_red":   "#8B0000",
            "white":      "#FFFFFF",
            "light_grey": "#E0E0E0"
        }

        self.root.configure(bg=self.palette["dark_grey"])

        self.f_header = ("Comic Sans MS", 20, "bold")
        self.f_norm = ("Verdana", 10, "bold")
        self.f_cute = ("Courier New", 11, "bold")

        self.login_entry_style = {
            "bg": self.palette["light_grey"],
            "fg": self.palette["dark_grey"],
            "font": ("Fixedsys", 12),
            "justify": 'center'
        }

        self.chat_handler = None
        self.user_alias = ""
        self.selected_contact = None
        self.message_log = {}
        self.active_users = []

        self.pending_msg_range = None

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.build_login()

    def add_chaos(self, canvas):
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            img_path = os.path.join(base_dir, "deadpool.png")
            if os.path.exists(img_path):
                deadpool_img = Image.open(img_path)
                deadpool_img = deadpool_img.resize((50, 50), Image.Resampling.LANCZOS)
                deadpool_photo = ImageTk.PhotoImage(deadpool_img)
                
                self.falling_items = []
                self.animation_canvas = canvas
                canvas_width = canvas.winfo_reqwidth() if canvas.winfo_reqwidth() > 1 else 500
                canvas_height = canvas.winfo_reqheight() if canvas.winfo_reqheight() > 1 else 500
                
                img_size = 50
                spacing_x = max(60, canvas_width / 10)
                spacing_y = max(80, canvas_height / 8)
                
                border_padding = 5
                
                used_positions = []
                for i in range(45):
                    attempts = 0
                    while attempts < 50:
                        x = random.uniform(border_padding, canvas_width - border_padding - img_size)
                        y = random.uniform(-canvas_height, 0)
                        
                        too_close = False
                        for px, py in used_positions:
                            if abs(x - px) < spacing_x and abs(y - py) < spacing_y:
                                too_close = True
                                break
                        
                        if not too_close:
                            used_positions.append((x, y))
                            img_id = canvas.create_image(x, y, image=deadpool_photo, anchor="nw")
                            canvas.image_refs = getattr(canvas, 'image_refs', [])
                            canvas.image_refs.append(deadpool_photo)
                            speed = random.uniform(3, 7)
                            self.falling_items.append({"id": img_id, "x": x, "y": y, "speed": speed})
                            break
                        attempts += 1
                
                self.animate_rain()
        except Exception:
            pass
    
    def animate_rain(self):
        if not hasattr(self, 'falling_items') or not hasattr(self, 'animation_canvas'):
            return
        
        try:
            canvas = self.animation_canvas
            if not canvas.winfo_exists():
                return
            
            canvas.update_idletasks()
            canvas_width = canvas.winfo_width() if canvas.winfo_width() > 1 else 500
            canvas_height = canvas.winfo_height() if canvas.winfo_height() > 1 else 500
        except:
            return
        
        img_size = 50
        spacing_x = max(60, canvas_width / 10)
        border_padding = 5
        
        for item in self.falling_items:
            item["y"] += item["speed"]
            if item["y"] > canvas_height + 50:
                item["y"] = -50
                
                attempts = 0
                new_x = random.uniform(border_padding, canvas_width - border_padding - img_size)
                while attempts < 50:
                    too_close = False
                    for other_item in self.falling_items:
                        if other_item != item and abs(new_x - other_item["x"]) < spacing_x:
                            too_close = True
                            break
                    
                    if not too_close:
                        break
                    new_x = random.uniform(border_padding, canvas_width - border_padding - img_size)
                    attempts += 1
                
                item["x"] = new_x
            canvas.coords(item["id"], item["x"], item["y"])
        
        self.root.after(30, self.animate_rain)

    # --- SCREENS ---
    def build_login(self):
        self.clear()

        container = tk.Frame(self.root, bg=self.palette["dark_red"], bd=10, relief="ridge")
        container.place(relx=0.5, rely=0.5, anchor="center", width=500, height=500)
        
        canvas_bg = tk.Canvas(container, bg=self.palette["dark_red"], highlightthickness=0)
        canvas_bg.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.add_chaos(canvas_bg)

        content_frame = tk.Frame(container, bg=self.palette["dark_grey"], bd=4, relief="solid")
        content_frame.place(relx=0.5, rely=0.5, anchor="center", width=350, height=400)
        
        self.main_content_frame = content_frame

        tk.Label(content_frame, text="LOGIN", bg=self.palette["dark_grey"],
                 fg=self.palette["dark_red"], font=self.f_header).pack(pady=10)

        tk.Label(content_frame, text="Nickname:", bg=self.palette["dark_grey"],
                 fg=self.palette["white"], font=self.f_norm).pack()
        self.input_nickname = tk.Entry(content_frame, **self.login_entry_style)
        self.input_nickname.pack(pady=5)

        tk.Label(content_frame, text="Server IP:", bg=self.palette["dark_grey"],
                 fg=self.palette["white"], font=self.f_norm).pack()
        self.input_server_ip = tk.Entry(content_frame, **self.login_entry_style)
        self.input_server_ip.insert(0, "192.168.0.106")
        self.input_server_ip.pack(pady=5)

        tk.Label(content_frame, text="Port:", bg=self.palette["dark_grey"],
                 fg=self.palette["white"], font=self.f_norm).pack()
        self.input_port_num = tk.Entry(content_frame, **self.login_entry_style)
        self.input_port_num.insert(0, "10000")
        self.input_port_num.pack(pady=5)

        login_btn = tk.Button(content_frame, text="LOGIN",
                        bg=self.palette["dark_red"], fg=self.palette["dark_grey"],
                        activebackground=self.palette["dark_red"],
                        activeforeground=self.palette["dark_grey"],
                        font=("Impact", 14), relief="raised", bd=4,
                        highlightthickness=0,
                        command=self.connect)
        login_btn.pack(pady=20)

    def connect(self):
        user_name = self.input_nickname.get().strip()
        server_host = self.input_server_ip.get().strip()
        port_value = self.input_port_num.get().strip()

        if not user_name:
            messagebox.showwarning("Oops", "Nickname missing!")
            return

        if not server_host or not port_value.isdigit():
            messagebox.showwarning("Oops", "Invalid IP or Port!")
            return

        # Create a FRESH logic instance for every attempt
        self.chat_handler = ChatLogic(server_host, int(port_value))

        result, response_msg = self.chat_handler.connect(user_name)
        if result:
            self.user_alias = user_name
            self.chat_handler.start_receiving(self.on_msg)
            self.build_chat()
        else:
            messagebox.showerror("FAIL", response_msg)

    def build_chat(self):
        self.clear()

        self.root.minsize(600, 450)

        deadpool_quotes = [
            "Maximum effort!",
            "With great power comes great irresponsibility.",
            "Life is an endless series of train wrecks.",
            "Fourth wall break inside a fourth wall break? That's like... sixteen walls.",
            "I may be super, but I'm no hero.",
            "You're welcome, Canada.",
            "I need you to be the angel on my shoulder, telling me not to do the dumb thing.",
            "That's such a fetch statement.",
            "Connection established. Maximum effort engaged!",
            "Server online. Client authenticated.",
            "Network protocol activated. Ready for chaos.",
            "TCP/IP: Totally Cool Protocol - Incredibly Powerful!",
            "Firewall? What firewall? I break walls for a living."
        ]
        mq = Marquee(self.root, deadpool_quotes, self.palette["dark_red"], self.palette["white"])
        mq.pack(side="top", fill="x")

        sidebar = tk.Frame(self.root, bg=self.palette["dark_red"], width=280, bd=5, relief="groove")
        sidebar.pack(side="left", fill="y", padx=5, pady=5)

        profile_frame = tk.Frame(sidebar, bg=self.palette["dark_red"], bd=3, relief="ridge", pady=10)
        profile_frame.pack(fill="x", padx=5, pady=(5, 10))

        tk.Label(profile_frame, text=self.user_alias, bg=self.palette["dark_red"],
                 fg=self.palette["white"], font=("Comic Sans MS", 14, "bold")).pack()

        tk.Label(profile_frame, text="How are you feeling today?", bg=self.palette["dark_red"],
                 fg=self.palette["white"], font=("Verdana", 8)).pack(pady=(5,0))

        self.status_input = tk.Entry(profile_frame, bg=self.palette["light_grey"], fg=self.palette["dark_grey"],
                                   font=("Arial", 9, "italic"), justify="center", bd=1)
        self.status_input.insert(0, "maximum effort")
        self.status_input.pack(fill="x", padx=10, pady=2)

        tk.Frame(sidebar, bg=self.palette["white"], height=2).pack(fill="x", padx=10, pady=5)

        tk.Label(sidebar, text="TEAMMATES", bg=self.palette["dark_red"], fg=self.palette["white"],
                 font=("Comic Sans MS", 16, "bold")).pack(pady=5)

        self.user_listbox = tk.Listbox(sidebar, bg=self.palette["light_grey"], fg=self.palette["dark_grey"],
                                    font=self.f_cute, selectbackground=self.palette["dark_red"],
                                    selectforeground=self.palette["white"], relief="sunken", bd=0)
        self.user_listbox.pack(fill="both", expand=True, padx=10, pady=5)
        self.user_listbox.bind("<<ListboxSelect>>", self.on_select_user)

        main_area = tk.Frame(self.root, bg=self.palette["dark_grey"])
        main_area.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        input_frame = tk.Frame(main_area, bg=self.palette["dark_grey"], bd=5, relief="flat", pady=8, padx=8)
        input_frame.pack(side="bottom", fill="x", pady=0)

        self.message_input = tk.Entry(input_frame, font=self.f_norm, bg=self.palette["light_grey"],
                                fg=self.palette["dark_grey"], bd=0, justify='left')
        self.message_input.pack(side="left", fill="x", expand=True, padx=(0, 10), ipady=5)
        self.message_input.bind("<Return>", lambda e: self.send())

        send_button = tk.Button(input_frame, text="SEND", bg=self.palette["dark_red"], fg=self.palette["dark_grey"],
                             activebackground=self.palette["dark_red"],
                             activeforeground=self.palette["dark_grey"],
                             font=("Impact", 12), command=self.send, bd=0, padx=15,
                             highlightthickness=0)
        send_button.pack(side="right")

        self.contact_label = tk.Label(main_area, text="Choose a teammate!",
                                   bg=self.palette["dark_grey"], fg=self.palette["dark_red"],
                                   font=("Comic Sans MS", 18, "bold"))
        self.contact_label.pack(side="top", pady=10)

        self.chat_display = tk.Text(main_area, bg=self.palette["light_grey"], fg=self.palette["dark_grey"],
                                font=("Comic Sans MS", 11), state="disabled",
                                relief="flat", bd=5)
        self.chat_display.pack(side="top", fill="both", expand=True, padx=5)

        self.chat_display.tag_config("me_ltr", foreground=self.palette["dark_red"], font=("Verdana", 10, "bold"), justify="left")
        self.chat_display.tag_config("them_ltr", foreground=self.palette["dark_grey"], font=("Verdana", 10, "bold"), justify="left")
        self.chat_display.tag_config("sys", foreground="gray", justify="center", font=("Arial", 9, "italic"))
        self.chat_display.tag_config("error", foreground="red", justify="center", font=("Arial", 10, "bold"))
        self.chat_display.tag_config("join", foreground="green", justify="center", font=("Arial", 8, "bold"))
        self.chat_display.tag_config("leave", foreground="red", justify="center", font=("Arial", 8, "bold"))

    def on_msg(self, msg):
        if msg.startswith("ONLINE_USERS:"):
            users_string = msg.replace("ONLINE_USERS:", "")
            updated_users = users_string.split(",") if users_string else []
            updated_users = [u for u in updated_users if u != self.user_alias]

            previous_set = set(self.active_users)
            current_set = set(updated_users)

            new_connections = current_set - previous_set
            disconnected = previous_set - current_set

            self.active_users = updated_users
            self.root.after(0, lambda: self.update_list_and_notify(new_connections, disconnected))

        elif msg.startswith("System:"):
            error_content = msg.split(":", 1)[1].strip()
            if "not found" in error_content or "no longer online" in error_content:
                self.root.after(0, self.delete_last_optimistic_message)
            messagebox.showerror("Oops!", error_content)

        elif ":" in msg:
            try:
                parts = msg.split(":", 1)
                sender = parts[0].strip("[] ")
                content = parts[1].strip()

                self.save_msg(sender, content, "them")
                if self.selected_contact == sender:
                    self.root.after(0, self.display_chat_message, sender, content, "them")
            except: pass

    def delete_last_optimistic_message(self):
        if self.pending_msg_range:
            start_pos, end_pos = self.pending_msg_range
            self.chat_display.config(state="normal")
            try:
                self.chat_display.delete(start_pos, end_pos)
            except tk.TclError:
                pass
            self.chat_display.config(state="disabled")

            if self.selected_contact in self.message_log:
                if self.message_log[self.selected_contact]:
                    self.message_log[self.selected_contact].pop()
            self.pending_msg_range = None

    def update_list_and_notify(self, joined, left):
        self.user_listbox.delete(0, tk.END)
        for user in self.active_users:
            self.user_listbox.insert(tk.END, "" + user)

        if self.selected_contact:
            for user in joined:
                if user == self.selected_contact:
                    self.display_system_msg(f"{user} is ONLINE\n", "join")

            for user in left:
                if user == self.selected_contact:
                    self.display_system_msg(f"{user} disconnected\n", "leave")

    def on_select_user(self, e):
        selection = self.user_listbox.curselection()
        if not selection: return
        selected_name = self.active_users[selection[0]]
        self.selected_contact = selected_name
        self.contact_label.config(text=f"{selected_name}")
        self.refresh_chat()

    def refresh_chat(self):
        self.chat_display.config(state="normal")
        self.chat_display.delete("1.0", tk.END)
        if self.selected_contact in self.message_log:
            for msg in self.message_log[self.selected_contact]:
                self.display_chat_message(msg['sender'], msg['content'], msg['type'], insert_mode=True)
        self.chat_display.see(tk.END)
        self.chat_display.config(state="disabled")

    def save_msg(self, partner, content, type_):
        if partner not in self.message_log: self.message_log[partner] = []
        display_name = "Me" if type_ == "me" else partner
        self.message_log[partner].append({"sender": display_name, "content": content, "type": type_})

    def send(self):
        if not self.selected_contact:
            messagebox.showinfo("Oops", "Pick a teammate before chatting!")
            return
        message_text = self.message_input.get().strip()
        if not message_text: return

        self.chat_handler.send_private_message(self.selected_contact, message_text)
        self.save_msg(self.selected_contact, message_text, "me")

        start_position = self.chat_display.index("end-1c")
        self.display_chat_message("Me", message_text, "me")
        end_position = self.chat_display.index("end-1c")
        self.pending_msg_range = (start_position, end_position)

        self.message_input.delete(0, tk.END)

    def display_chat_message(self, sender, raw_content, base_type, insert_mode=False):
        if not insert_mode:
            self.chat_display.config(state="normal")
        message_tag = base_type + "_ltr"
        formatted_line = f"{sender}: {raw_content}\n"
        self.chat_display.insert(tk.END, formatted_line, message_tag)
        if not insert_mode:
            self.chat_display.see(tk.END)
            self.chat_display.config(state="disabled")

    def display_system_msg(self, txt, tag):
        self.chat_display.config(state="normal")
        self.chat_display.insert(tk.END, txt + "\n", tag)
        self.chat_display.see(tk.END)
        self.chat_display.config(state="disabled")

    def clear(self):
        for w in self.root.winfo_children(): w.destroy()

    def on_closing(self):
        if self.chat_handler:
            self.chat_handler.disconnect()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = Y2KPinkPaletteGUI(root)
    root.mainloop()
