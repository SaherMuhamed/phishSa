#!/usr/bin/env python3

import sys
import time
import subprocess
import json
import os
import re

from colorama import Style, Fore
from utilities.dashboard import dashboard
from utilities.constants import CLIENT_CONNECTED


def stop_network_services():
    try:
        subprocess.run(["systemctl", "stop", "NetworkManager"], check=True)
        print("[✔] Stopped network services")
    except subprocess.CalledProcessError as e:
        print(f"[-] Error stopping network services: {e}")
        sys.exit(1)


def setup_interface(interface):
    try:
        subprocess.run(["ifconfig", interface, "192.168.1.1", "netmask", "255.255.255.0"], check=True)
        print(f"[✔] Configured {interface} to use wireless connectivity")
    except subprocess.CalledProcessError as e:
        print(f"[-] Error configuring interface: {e}")
        sys.exit(1)


def load_oui_database(json_path="settings/mac-vendors-export.json"):
    mac_vendors = {}
    if not os.path.exists(json_path):
        print(f"[-] OUI database not found at {json_path}")
        return mac_vendors
    
    try:
        with open(json_path, "r") as f:
            oui_data = json.load(f)
            
            if not isinstance(oui_data, list):
                print("[-] Invalid OUI JSON format: Expected list of entries")
                return mac_vendors
                
            for entry in oui_data:
                try:
                    prefix = entry.get("macPrefix", "").strip().upper()
                    prefix = ":".join([x.zfill(2) for x in re.split(r"[-:]", prefix)[:3]])
                    vendor = entry.get("vendorName", "").strip()
                    
                    if len(prefix) == 8 and vendor:
                        mac_vendors[prefix] = vendor
                except (AttributeError, KeyError):
                    continue
                    
    except json.JSONDecodeError:
        print("[-] Invalid JSON file format")
    except Exception as e:
        print(f"[-] Error loading OUI DB: {str(e)}")
        
    return mac_vendors

def lookup_vendor(mac, vendors):
    if not mac or not vendors:
        return "Unknown"
    
    try:
        mac = mac.strip().upper()
        hex_chars = re.sub(r"[^0-9A-F]", "", mac)[:6]
        if len(hex_chars) != 6:
            return "Unknown"
            
        prefix = ":".join([hex_chars[i:i+2] for i in range(0, 6, 2)])
        return vendors.get(prefix, "Unknown")
        
    except Exception:
        return "Unknown"


def monitor_clients(interface):
    global CLIENT_CONNECTED
    seen_macs = set()
    vendors = load_oui_database("settings/mac-vendors-export.json")

    while True:
        result = subprocess.run(["iw", "dev", interface, "station", "dump"], capture_output=True, text=True)
        output = result.stdout

        stations = output.split("Station ")[1:] if "Station " in output else []

        if stations:
            if not CLIENT_CONNECTED:
                print(Fore.GREEN + "\n ⬤ Client connected! Phishing page is being served" + Style.RESET_ALL)
                dashboard.log_activity("Client connected to AP", "success")
                CLIENT_CONNECTED = True

            for station_data in stations:
                lines = station_data.strip().split("\n")
                mac = lines[0].strip()
                signal_line = [line for line in lines if "signal:" in line]
                signal_strength = signal_line[0].split(":")[1].strip() if signal_line else "N/A"
                vendor = lookup_vendor(mac, vendors)

                if mac not in seen_macs:
                    print(Fore.YELLOW + f"\n📡 New client detected")
                    print(f" ├─ MAC: {mac}")
                    print(f" ├─ Vendor: {vendor}")
                    print(f" └─ Signal: {signal_strength}" + Style.RESET_ALL)

                    dashboard.log_activity(f"New client detected: {mac} ({vendor})")
                    seen_macs.add(mac)

                dashboard.update_client({
                    'mac': mac,
                    'vendor': vendor,
                    'signal': signal_strength,
                    'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
                })

        else:
            if CLIENT_CONNECTED:
                print(Fore.RED + "\n ⬤ Client disconnected. Waiting for new clients..." + Style.RESET_ALL)
                dashboard.log_activity("Client disconnected", "warning")
                CLIENT_CONNECTED = False
            seen_macs.clear()

        time.sleep(2)
