import os
import sys
import json
import subprocess
import customtkinter as ctk
from tkinter import filedialog, messagebox
import psutil
from PIL import Image

CONFIG_FILE = "dashboard_config.json"

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(BASE_DIR, CONFIG_FILE)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ShortcutDialog(ctk.CTkToplevel):
    def __init__(self, parent, callback, shortcut=None):
        super().__init__(parent)
        self.title("Shortcut Details")
        self.geometry("400x350")
        self.resizable(False, False)
        
        self.transient(parent)
        self.grab_set()
        self.focus()

        self.callback = callback
        self.shortcut = shortcut

        self.name_var = ctk.StringVar(value=shortcut["name"] if shortcut else "")
        self.path_var = ctk.StringVar(value=shortcut["path"] if shortcut else "")
        self.img_var = ctk.StringVar(value=shortcut["image"] if shortcut and "image" in shortcut else "")

        ctk.CTkLabel(self, text="Name:").pack(pady=(20, 5), padx=20, anchor="w")
        ctk.CTkEntry(self, textvariable=self.name_var, width=360).pack(padx=20)

        ctk.CTkLabel(self, text="File Path (.exe, .lnk, etc):").pack(pady=(10, 5), padx=20, anchor="w")
        frame_path = ctk.CTkFrame(self, fg_color="transparent")
        frame_path.pack(padx=20, fill="x")
        ctk.CTkEntry(frame_path, textvariable=self.path_var).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(frame_path, text="Browse", width=80, command=self.browse_file).pack(side="right", padx=(10, 0))

        ctk.CTkLabel(self, text="Image Path (.png, .jpg) - Optional:").pack(pady=(10, 5), padx=20, anchor="w")
        frame_img = ctk.CTkFrame(self, fg_color="transparent")
        frame_img.pack(padx=20, fill="x")
        ctk.CTkEntry(frame_img, textvariable=self.img_var).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(frame_img, text="Browse", width=80, command=self.browse_image).pack(side="right", padx=(10, 0))

        ctk.CTkButton(self, text="Save", command=self.save, height=40, font=ctk.CTkFont(weight="bold")).pack(pady=30, padx=20, fill="x")

    def browse_file(self):
        path = filedialog.askopenfilename(title="Select Application")
        if path:
            self.path_var.set(path)
            if not self.name_var.get():
                self.name_var.set(os.path.basename(path).split('.')[0].capitalize())

    def browse_image(self):
        path = filedialog.askopenfilename(title="Select Image", filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if path:
            self.img_var.set(path)

    def save(self):
        name = self.name_var.get().strip()
        path = self.path_var.get().strip()
        img = self.img_var.get().strip()

        if not name or not path:
            messagebox.showerror("Error", "Name and File Path are required.", parent=self)
            return

        self.callback({"name": name, "path": path, "image": img}, self.shortcut)
        self.destroy()


class ZoroDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ZORO DASHBOARD88 - MC88")
        self.geometry("1000x650")
        self.minsize(900, 600)

        self.shortcuts = self.load_config()
        self.current_dialog = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_sidebar()
        self.build_main_area()

    def build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#1a1a1a")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(9, weight=1)

        ctk.CTkLabel(self.sidebar, text="ZORO88", font=ctk.CTkFont(size=28, weight="bold"), text_color="#3498db").grid(row=0, column=0, padx=20, pady=(30, 5))
        ctk.CTkLabel(self.sidebar, text="System Dashboard", font=ctk.CTkFont(size=12), text_color="gray").grid(row=1, column=0, padx=20, pady=(0, 30))

        ctk.CTkLabel(self.sidebar, text="SYSTEM CONTROLS", font=ctk.CTkFont(size=11, weight="bold"), text_color="#555555").grid(row=2, column=0, padx=20, pady=(10, 10), sticky="w")

        self.create_sys_btn("Shutdown", "#c0392b", self.sys_shutdown).grid(row=3, column=0, padx=20, pady=5)
        self.create_sys_btn("Restart", "#e67e22", self.sys_restart).grid(row=4, column=0, padx=20, pady=5)
        self.create_sys_btn("Close All Windows", "#8e44ad", self.sys_close_all).grid(row=5, column=0, padx=20, pady=5)
        self.create_sys_btn("Kill Top 10 Apps", "#2980b9", self.sys_kill_heavy).grid(row=6, column=0, padx=20, pady=5)
        
        ctk.CTkLabel(self.sidebar, text="COPYRIGHT: MC88", font=ctk.CTkFont(size=10), text_color="gray").grid(row=10, column=0, padx=20, pady=20)

    def create_sys_btn(self, text, color, command):
        return ctk.CTkButton(self.sidebar, text=text, fg_color=color, hover_color="#2c3e50", command=command, height=45, font=ctk.CTkFont(weight="bold"))

    def build_main_area(self):
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.grid_rowconfigure(1, weight=1)

        top_bar = ctk.CTkFrame(self.main_area, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        ctk.CTkLabel(top_bar, text="MY SHORTCUTS", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")
        ctk.CTkButton(top_bar, text="+ Add New Shortcut", command=self.add_shortcut, width=160).pack(side="right")

        self.scroll_frame = ctk.CTkScrollableFrame(self.main_area, fg_color="#242424", corner_radius=15)
        self.scroll_frame.grid(row=1, column=0, sticky="nsew")
        
        self.render_shortcuts()

    def render_shortcuts(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        for idx, sc in enumerate(self.shortcuts):
            row = idx // 3
            col = idx % 3
            self.scroll_frame.grid_columnconfigure(col, weight=1)

            card = ctk.CTkFrame(self.scroll_frame, fg_color="#1e1e1e", corner_radius=10, border_width=1, border_color="#333333")
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            img_label = ctk.CTkLabel(card, text="")
            img_label.pack(pady=(15, 5))
            
            try:
                if sc.get("image") and os.path.exists(sc["image"]):
                    img = ctk.CTkImage(light_image=Image.open(sc["image"]), dark_image=Image.open(sc["image"]), size=(64, 64))
                    img_label.configure(image=img, text="")
                else:
                    img_label.configure(text="📁", font=ctk.CTkFont(size=48))
            except Exception:
                img_label.configure(text="📁", font=ctk.CTkFont(size=48))

            ctk.CTkLabel(card, text=sc["name"], font=ctk.CTkFont(size=14, weight="bold"), wraplength=180).pack(pady=5)

            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(fill="x", padx=15, pady=(5, 15))

            ctk.CTkButton(btn_frame, text="Open", width=70, command=lambda s=sc: self.run_shortcut(s)).pack(side="left", expand=True)
            ctk.CTkButton(btn_frame, text="Edit", width=50, fg_color="#444444", command=lambda s=sc: self.edit_shortcut(s)).pack(side="left", expand=True, padx=5)
            ctk.CTkButton(btn_frame, text="X", width=30, fg_color="#c0392b", hover_color="#e74c3c", command=lambda i=idx: self.delete_shortcut(i)).pack(side="right")

    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save_config(self):
        with open(CONFIG_PATH, "w") as f:
            json.dump(self.shortcuts, f, indent=4)

    def add_shortcut(self):
        self.current_dialog = ShortcutDialog(self, self.save_shortcut_callback)

    def edit_shortcut(self, shortcut):
        self.current_dialog = ShortcutDialog(self, self.save_shortcut_callback, shortcut)

    def save_shortcut_callback(self, data, old_shortcut):
        if old_shortcut:
            idx = self.shortcuts.index(old_shortcut)
            self.shortcuts[idx] = data
        else:
            self.shortcuts.append(data)
        self.save_config()
        self.render_shortcuts()

    def delete_shortcut(self, idx):
        if messagebox.askyesno("Confirm", "Delete this shortcut?"):
            del self.shortcuts[idx]
            self.save_config()
            self.render_shortcuts()

    def run_shortcut(self, shortcut):
        try:
            os.startfile(shortcut["path"])
        except Exception as e:
            messagebox.showerror("Error", f"Could not launch {shortcut['name']}\n{e}")

    def sys_shutdown(self):
        if messagebox.askyesno("Shutdown", "Are you sure you want to shutdown the PC?"):
            os.system("shutdown /s /t 3")

    def sys_restart(self):
        if messagebox.askyesno("Restart", "Are you sure you want to restart the PC?"):
            os.system("shutdown /r /t 3")

    def sys_close_all(self):
        if messagebox.askyesno("Warning", "Force close all open applications?"):
            protected = ['explorer.exe', 'python.exe', 'main.exe', 'zoro.exe', 'winlogon.exe', 'csrss.exe', 'svchost.exe', 'taskhostw.exe']
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] and proc.info['name'].lower() not in protected:
                        proc.kill()
                except Exception:
                    pass
            messagebox.showinfo("Done", "All windows closed.")

    def sys_kill_heavy(self):
        if messagebox.askyesno("Warning", "Kill the top 10 memory-consuming apps?"):
            apps = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
                try:
                    if proc.info['name'] and proc.info['name'].lower() not in ['explorer.exe', 'python.exe', 'main.exe', 'zoro.exe']:
                        apps.append(proc.info)
                except Exception:
                    pass
            
            apps.sort(key=lambda x: x['memory_percent'], reverse=True)
            for app in apps[:10]:
                try:
                    p = psutil.Process(app['pid'])
                    p.kill()
                except Exception:
                    pass
            messagebox.showinfo("Done", "Top 10 heavy apps have been terminated.")

if __name__ == "__main__":
    app = ZoroDashboard()
    app.mainloop()
