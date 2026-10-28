import sys
import traceback
import threading

def start_app():
    import customtkinter as ctk
    import pystray
    from PIL import Image, ImageDraw
    import zoro

    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    class ZoroApp(ctk.CTk):
        def __init__(self):
            super().__init__()
            self.title("Zoro Voice Assistant - MC88")
            self.geometry("400x300")
            self.resizable(False, False)

            self.status_label = ctk.CTkLabel(self, text="Status: Sleeping", font=("Arial", 20, "bold"))
            self.status_label.pack(pady=40)

            self.log_label = ctk.CTkLabel(self, text="Waiting for 'Zoro wake up'...", font=("Arial", 14))
            self.log_label.pack(pady=10)

            self.protocol('WM_DELETE_WINDOW', self.hide_window)
            self.create_tray_icon()

            threading.Thread(target=zoro.main_loop, args=(self.update_ui,), daemon=True).start()

        def update_ui(self, text):
            if "Awake" in text:
                self.status_label.configure(text="Status: Awake", text_color="green")
            elif "Sleeping" in text:
                self.status_label.configure(text="Status: Sleeping", text_color="gray")
            self.log_label.configure(text=text)

        def hide_window(self):
            self.withdraw()

        def show_window(self, icon, item):
            self.deiconify()

        def quit_app(self, icon, item):
            icon.stop()
            self.destroy()

        def create_tray_icon(self):
            image = Image.new('RGB', (64, 64), color='black')
            d = ImageDraw.Draw(image)
            d.ellipse((16, 16, 48, 48), fill='blue')
            
            menu = pystray.Menu(
                pystray.MenuItem("Show", self.show_window),
                pystray.MenuItem("Quit", self.quit_app)
            )
            self.icon = pystray.Icon("Zoro", image, "Zoro Assistant", menu)
            threading.Thread(target=self.icon.run, daemon=True).start()

    app = ZoroApp()
    app.mainloop()

if __name__ == "__main__":
    try:
        start_app()
    except Exception:
        with open("crash_log.txt", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
