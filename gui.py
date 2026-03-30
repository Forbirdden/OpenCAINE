import os
import subprocess
import shutil
import time
import threading
import sys
import platform
import psutil # Если нет, сделай pip install psutil, или я заменю на стандартные
from tkinterdnd2 import DND_FILES, TkinterDnD
import customtkinter as ctk
from PIL import Image

ctk.set_appearance_mode("dark")

class CaineInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("Cmd")
        self.font_name = "Courier"

        self.root.geometry("1280x720")
        self.root.configure(bg="black")
        self.root.resizable(False, False)

        os.makedirs("INPUT", exist_ok=True)
        if os.path.exists("SIGNAL.txt"): os.remove("SIGNAL.txt")

        # --- 1. BOOT TERMINAL ---
        self.boot_frame = ctk.CTkFrame(self.root, fg_color="black", corner_radius=0)
        self.boot_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        self.terminal = ctk.CTkTextbox(self.boot_frame, fg_color="black", text_color="#cccccc", 
                                      font=(self.font_name, 14), border_width=0, 
                                      padx=10, pady=10, activate_scrollbars=False)
        self.terminal.pack(fill="both", expand=True)

        # --- 2. MAIN INTERFACE ---
        self.main_frame = ctk.CTkFrame(self.root, fg_color="black", corner_radius=0)
        # Настройка сетки (фиксированные размеры)
        self.main_frame.grid_columnconfigure(0, weight=1, minsize=440)
        self.main_frame.grid_columnconfigure(1, weight=0, minsize=200)
        self.main_frame.grid_columnconfigure(2, weight=1, minsize=440)
        self.main_frame.grid_rowconfigure(0, weight=1)

        self.left_label = ctk.CTkLabel(self.main_frame, text="[ PAST ]", width=400, height=400, 
                                      font=("Courier", 20), text_color="white")
        self.left_label.grid(row=0, column=0)

        # --- ЦЕНТРАЛЬНАЯ ПАНЕЛЬ (The Core) ---
        self.center_container = ctk.CTkFrame(self.main_frame, fg_color="black", width=200)
        self.center_container.grid(row=0, column=1)

        # Создаем холст для свечения
        self.glow_canvas = ctk.CTkCanvas(self.center_container, width=140, height=140, 
                                        bg="black", highlightthickness=0)
        self.glow_canvas.pack(pady=20)

        # Рисуем свечение (слои от прозрачного к яркому)
        def draw_glow(canvas):
            x, y, r = 70, 70, 60
            # Рисуем 10 слоев затухания
            for i in range(r, 25, -4):
                alpha = int(255 * (1 - i/r)**2) # Квадратичное затухание
                color = f'#{alpha:02x}0000' # Постепенное превращение в красный
                canvas.create_oval(x-i, y-i, x+i, y+i, fill=color, outline="")
            
            # Центральное ядро (самое яркое)
            canvas.create_oval(x-25, y-25, x+25, y+25, fill="#FF0000", outline="#FF6666", width=2)

        draw_glow(self.glow_canvas)

        # Делаем холст кликабельным
        self.glow_canvas.bind("<Button-1>", lambda e: self.run_lisp())
        # Курсор при наведении
        self.glow_canvas.configure(cursor="hand2")

        
        self.status = ctk.CTkLabel(self.center_container, text="DRAG & DROP IMAGES", font=("Courier", 14), text_color="white")
        self.status.pack()

        self.right_label = ctk.CTkLabel(self.main_frame, text="[ PRESENT ]", width=400, height=400, 
                                       font=("Courier", 20), text_color="white")
        self.right_label.grid(row=0, column=2)

        self.start_lisp_and_monitor()

    def insert_log(self, text, delay=0.01):
        """Плавная печать логов"""
        self.terminal.insert("end", text + "\n")
        self.terminal.see("end")
        self.root.update()
        time.sleep(delay)

    def start_lisp_and_monitor(self):
        def boot_sequence():
            self.insert_log(f"[SYS]: OS: {platform.system()} {platform.release()} ({platform.machine()})")
            self.insert_log(f"[SYS]: PROCESSOR: {platform.processor()}")
            self.insert_log(f"[SYS]: DIRECTORY: {os.getcwd()}")
            self.insert_log("[SYS]: STARTING STEEL BANK COMMON LISP COMPILER...")
            self.insert_log("")

            # Запуск Липса
            self.lisp_proc = subprocess.Popen(
                ["sbcl", "--load", "caine-core.lisp"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Перехват вывода Липса
            for line in iter(self.lisp_proc.stdout.readline, ''):
                self.terminal.insert("end", f"[SBCL]: {line}")
                self.terminal.see("end")
                self.root.update()
                if "ENGINE ONLINE" in line or "AWAITING SIGNAL" in line:
                    self.insert_log("[CAINE]: HANDSHAKE ACCEPTED. OPENING INTERFACE...")
                    time.sleep(1.5)
                    self.show_main_ui()
                    break

        threading.Thread(target=boot_sequence, daemon=True).start()

    def show_main_ui(self):
        self.boot_frame.place_forget()
        self.main_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.handle_drop)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # ... (handle_drop, run_lisp, on_closing остаются без изменений)
    def handle_drop(self, event):
        data = event.data.strip('{}')
        files = self.root.tk.splitlist(data)
        existing_files = os.listdir("INPUT")
        current_count = len([f for f in existing_files if f.endswith('.png')])
        for f in files:
            try:
                current_count += 1
                img = Image.open(f).convert("RGB")
                img = img.resize((128, 128), Image.Resampling.LANCZOS)
                img.save(f"INPUT/{current_count}.png", "PNG")
            except: pass
        self.status.configure(text=f"TRAINING IMAGES COUNT:{current_count}", text_color="white")

    def run_lisp(self):
        if os.path.exists("output.png"):
            past_raw = Image.open("output.png")
            past_img = ctk.CTkImage(light_image=past_raw, size=(400, 400))
            self.left_label.configure(image=past_img, text="")
        with open("SIGNAL.txt", "w") as f: f.write("GO")
        self.status.configure(text="GENERATING", text_color="white")
        def check_result():
            if not os.path.exists("SIGNAL.txt"):
                if os.path.exists("output.png"):
                    time.sleep(0.1)
                    curr_raw = Image.open("output.png")
                    curr_raw.load()
                    curr_img = ctk.CTkImage(light_image=curr_raw, size=(400, 400))
                    self.right_label.configure(image=curr_img, text="")
                    self.status.configure(text="READY", text_color="white")
            else: self.root.after(100, check_result)
        check_result()

    def on_closing(self):
        try: self.lisp_proc.terminate()
        except: pass
        self.root.destroy()

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = CaineInterface(root)
    root.mainloop()
