import winreg
import os

def get_installed_apps():
    apps = {}
    paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths")
    ]
    
    for hive, path in paths:
        try:
            key = winreg.OpenKey(hive, path)
            for i in range(winreg.QueryInfoKey(key)[0]):
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    subkey = winreg.OpenKey(key, subkey_name)
                    exe_path, _ = winreg.QueryValueEx(subkey, "")
                    if exe_path and exe_path.endswith(".exe"):
                        app_name = subkey_name.lower().replace(".exe", "")
                        apps[app_name] = exe_path
                except WindowsError:
                    continue
        except WindowsError:
            continue
    return apps
