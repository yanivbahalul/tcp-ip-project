import tkinter as tk
from tkinter import messagebox
import sys
import random
import os
from PIL import Image, ImageTk
from server import ServerLogic


class Marquee(tk.Canvas):
    def __init__(self, parent, text, bg, fg):
        super().__init__(parent, bg=bg, height=30, highlightthickness=0)
        self.text = text
        self.fg = fg
        self.width = 600
        self.text_obj = self.create_text(0, 15, text=text, fill=fg, font=("Comic Sans MS", 12, "bold"), anchor='w')
        self.animate()

    def animate(self):
        self.move(self.text_obj, -2, 0)
        bbox = self.bbox(self.text_obj)
        if bbox[2] < 0:
            self.coords(self.text_obj, self.width, 15)
        self.after(50, self.animate)

class TextRedirector(object):
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag

    def write(self, str):
        try:
            self.widget.configure(state="normal")
            self.widget.insert("end", str, (self.tag,))
            self.widget.see("end")
            self.widget.configure(state="disabled")
        except:
            pass

    def flush(self):
        pass

class PinkServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CONTROL ROOM")
        self.root.geometry("600x550")

        self.palette = {
            "dark_grey":  "#2C2C2C",
            "dark_red":   "#8B0000",
            "white":      "#FFFFFF",
            "light_grey": "#E0E0E0"
        }

        self.root.configure(bg=self.palette["dark_grey"])

        # Fonts
        self.f_header = ("Comic Sans MS", 20, "bold")
        self.f_norm = ("Verdana", 10, "bold")
        self.f_console = ("Courier New", 10, "bold")

        # Entry Style (Like Client)
        self.entry_style = {
            "bg": self.palette["light_grey"],
            "fg": self.palette["dark_grey"],
            "font": ("Fixedsys", 12),
            "justify": 'center'
        }

        self.server_handler = None

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.build_config_screen()

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
                canvas_height = canvas.winfo_reqheight() if canvas.winfo_reqheight() > 1 else 450
                
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
            canvas_height = canvas.winfo_height() if canvas.winfo_height() > 1 else 450
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

    def clear(self):
        for w in self.root.winfo_children(): w.destroy()

    def build_config_screen(self):
        self.clear()
        container = tk.Frame(self.root, bg=self.palette["dark_red"], bd=10, relief="ridge")
        container.place(relx=0.5, rely=0.5, anchor="center", width=500, height=450)
        
        canvas_bg = tk.Canvas(container, bg=self.palette["dark_red"], highlightthickness=0)
        canvas_bg.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.add_chaos(canvas_bg)

        content_frame = tk.Frame(container, bg=self.palette["dark_grey"], bd=4, relief="solid")
        content_frame.place(relx=0.5, rely=0.5, anchor="center", width=350, height=300)

        tk.Label(content_frame, text="SERVER CONFIG", bg=self.palette["dark_grey"],
                 fg=self.palette["dark_red"], font=self.f_header).pack(pady=20)

        tk.Label(content_frame, text="Binding IP Address:", bg=self.palette["dark_grey"],
                 fg=self.palette["white"], font=self.f_norm).pack()
        self.input_bind_ip = tk.Entry(content_frame, **self.entry_style)
        self.input_bind_ip.insert(0, "0.0.0.0")
        self.input_bind_ip.pack(pady=5)

        tk.Label(content_frame, text="Listening Port:", bg=self.palette["dark_grey"],
                 fg=self.palette["white"], font=self.f_norm).pack()
        self.input_listen_port = tk.Entry(content_frame, **self.entry_style)
        self.input_listen_port.insert(0, "10000")
        self.input_listen_port.pack(pady=5)
        start_server_btn = tk.Button(content_frame, text="RUN SERVER",
                        bg=self.palette["dark_red"], fg=self.palette["dark_grey"],
                        activebackground=self.palette["dark_red"],
                        activeforeground=self.palette["dark_grey"],
                        font=("Impact", 14), relief="raised", bd=4,
                        highlightthickness=0,
                        command=self.start_server_action)
        start_server_btn.pack(pady=25)

    def start_server_action(self):
        bind_address = self.input_bind_ip.get().strip()
        port_string = self.input_listen_port.get().strip()

        if not bind_address or not port_string.isdigit():
            messagebox.showerror("Oops", "Invalid IP or Port!")
            return

        listen_port = int(port_string)

        self.build_console_screen()

        sys.stdout = TextRedirector(self.log_area, "stdout")
        sys.stderr = TextRedirector(self.log_area, "stderr")

        self.server_handler = ServerLogic(bind_address, listen_port)

        def log_callback(message):
            self.log_area.configure(state="normal")
            self.log_area.insert("end", message + "\n")
            self.log_area.see("end")
            self.log_area.configure(state="disabled")

        self.server_handler.start_async(on_log=log_callback)

    def build_console_screen(self):
        self.clear()
        self.root.configure(bg=self.palette["dark_grey"])

        marquee_txt = "SERVER ONLINE    SERVER ONLINE    SERVER ONLINE    SERVER ONLINE   SERVER ONLINE    SERVER ONLINE    SERVER ONLINE    SERVER ONLINE"
        mq = Marquee(self.root, marquee_txt, self.palette["dark_red"], self.palette["white"])
        mq.pack(side="top", fill="x")

        container = tk.Frame(self.root, bg=self.palette["dark_grey"], bd=5, relief="ridge")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(container, text="SYSTEM LOGS", bg=self.palette["dark_grey"],
                 fg=self.palette["dark_red"], font=self.f_header).pack(pady=10)

        console_frame = tk.Frame(container, bg=self.palette["dark_red"], bd=2)
        console_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.log_area = tk.Text(console_frame, bg=self.palette["light_grey"], fg=self.palette["dark_grey"],
                                font=self.f_console, state="disabled", bd=5, relief="flat")
        self.log_area.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(self.log_area, command=self.log_area.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_area['yscrollcommand'] = scrollbar.set
        button_frame = tk.Frame(container, bg=self.palette["dark_grey"])
        button_frame.pack(fill="x", pady=10)

        check_users_btn = tk.Button(button_frame, text="CHECK ONLIONE USERS",
                                bg=self.palette["light_grey"], fg=self.palette["dark_grey"],
                                activebackground=self.palette["light_grey"],
                                activeforeground=self.palette["dark_grey"],
                                font=("Impact", 12), relief="raised", bd=3,
                                highlightthickness=0,
                                command=self.show_users)
        check_users_btn.pack(side="bottom", pady=5)

    def show_users(self):
        if not self.server_handler:
            print("Server not running!")
            return

        print("\n--- Online Users ---")
        online_list = self.server_handler.get_online_users()

        if not online_list:
            print("No users online")
        else:
            for user_info in online_list:
                if user_info["address"]:
                    print(f"{user_info['nickname']} - IP: {user_info['address']}")
                else:
                    print(f"{user_info['nickname']} (no address)")
        print("--- End List ---\n")

    def on_closing(self):
        if self.server_handler:
            self.server_handler.stop()

        sys.stdout = sys.__stdout__
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PinkServerGUI(root)
    root.mainloop()
