import os
import subprocess
import ctypes
import psutil
import winreg
import win32gui
import win32con
from datetime import datetime

try:
    from pycaw.pycaw import AudioUtilities
    _spk = AudioUtilities.GetSpeakers()
    _vol_api = _spk.EndpointVolume
    HAS_VOL = True
except Exception:
    HAS_VOL = False
    _vol_api = None

def set_volume(v):
    v = max(0, min(100, int(v)))
    if HAS_VOL:
        try:
            _vol_api.SetMasterVolumeLevelScalar(v / 100, None)
        except Exception:
            pass

def get_volume():
    if not HAS_VOL:
        return 50
    try:
        return int(_vol_api.GetMasterVolumeLevelScalar() * 100)
    except Exception:
        return 50

def volume_delta(d):
    set_volume(get_volume() + d)

def open_app(app_path):
    try:
        subprocess.Popen(f'"{app_path}"', shell=True)
        return True
    except Exception:
        return False

def force_close_all_windows():
    try:
        for proc in psutil.process_iter(['pid', 'name', 'username']):
            if proc.info['username'] == os.getlogin() and proc.info['name'] not in ['explorer.exe', 'python.exe', 'main.exe']:
                proc.kill()
        return True
    except Exception:
        return False

def close_active_window():
    try:
        hwnd = win32gui.GetForegroundWindow()
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        return True
    except Exception:
        return False

def set_theme(mode):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", 0, winreg.KEY_SET_VALUE)
        value = 1 if mode == "light" else 0
        winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, value)
        winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, value)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False

def lock_screen():
    ctypes.windll.user32.LockWorkStation()

def shutdown_pc():
    os.system("shutdown /s /t 5")

def restart_pc():
    os.system("shutdown /r /t 5")

def sleep_pc():
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

def get_time():
    return datetime.now().strftime("It's %I:%M %p")

def get_date():
    return datetime.now().strftime("Today is %A, %B %d")

def help_text():
    return "I can open apps, close windows, lock, shutdown, restart, and switch themes."
