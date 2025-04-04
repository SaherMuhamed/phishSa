#!/usr/bin/env python3

import sys


def configure_dnsmasq(interface):
    config = f"""
interface={interface}
dhcp-range=192.168.1.10,192.168.1.250,255.255.255.0,12h
dhcp-option=3,192.168.1.1
dhcp-option=6,192.168.1.1
server=8.8.8.8

# Only redirect HTTP traffic (port 80)
address=/#/192.168.1.1

# Special redirects for HTTP only
address=/captive.apple.com/192.168.1.1
address=/www.apple.com/192.168.1.1
address=/connectivitycheck.android.com/192.168.1.1
address=/clients3.google.com/192.168.1.1
address=/www.msftconnecttest.com/192.168.1.1

log-queries
log-dhcp
"""
    try:
        with open("settings/dnsmasq.conf", "w") as f:
            f.write(config)
        # print("[+] Configured dnsmasq for HTTP-only redirection")
    except IOError as e:
        print(f"[-] Error configuring dnsmasq: {e}")
        sys.exit(1)


def configure_hostapd(ssid, channel, interface):
    config = f"""
interface={interface}
driver=nl80211
ssid={ssid}
hw_mode=g
channel={channel}
auth_algs=1
# Beacon interval for faster detection
beacon_int=100
# Send empty SSID in beacons (some devices connect faster)
ignore_broadcast_ssid=0
"""
    try:
        with open("settings/hostapd.conf", "w") as f:
            f.write(config)
        # print("[+] Configured hostapd")
    except IOError as e:
        print(f"[-] Error configuring hostapd: {e}")
        sys.exit(1)
