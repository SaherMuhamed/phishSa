#!/usr/bin/env python3

import os
import sys


def configure_dnsmasq(interface):
    config = f"""
interface={interface}
dhcp-range=192.168.1.10,192.168.1.250,255.255.255.0,12h
dhcp-option=3,192.168.1.1
dhcp-option=6,192.168.1.1

# DNS servers (we'll intercept these queries)
server=8.8.8.8
server=1.1.1.1

# Global HTTP redirect (all domains to our portal)
address=/#/192.168.1.1

# Universal Captive Portal Detection Endpoints
address=/captive.apple.com/192.168.1.1
address=/apple.com/192.168.1.1
address=/www.apple.com/192.168.1.1
address=/gsp1.apple.com/192.168.1.1
address=/connectivitycheck.android.com/192.168.1.1
address=/clients3.google.com/192.168.1.1
address=/clients4.google.com/192.168.1.1
address=/play.googleapis.com/192.168.1.1
address=/www.google.com/192.168.1.1
address=/www.msftconnecttest.com/192.168.1.1
address=/msftconnecttest.com/192.168.1.1
address=/connectivitycheck.gstatic.com/192.168.1.1
address=/network-test.debian.org/192.168.1.1
address=/detectportal.firefox.com/192.168.1.1
address=/nmcheck.gnome.org/192.168.1.1
address=/captiveportal.konqi.de/192.168.1.1
address=/wifi.vodafone.com/192.168.1.1
address=/wifi.att.com/192.168.1.1

# Additional Android endpoints
address=/android.clients.google.com/192.168.1.1
address=/tools.google.com/192.168.1.1

# Additional Windows endpoints
address=/dns.msftncsi.com/192.168.1.1
address=/ipv6.msftncsi.com/192.168.1.1

# Additional Apple endpoints
address=/appspot.com/192.168.1.1
address=/itools.info/192.168.1.1
address=/ibook.info/192.168.1.1
address=/airport.us/192.168.1.1
address=/thinkdifferent.us/192.168.1.1
"""
    try:
        os.makedirs("settings", exist_ok=True)
        with open("settings/dnsmasq.conf", "w") as f:
            f.write(config)
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

# Security (open network)
auth_algs=1
wpa=0

# Beacon and probe response optimization
beacon_int=100          # Faster beacon interval (default is 100ms)
dtim_period=2           # More frequent DTIM frames
# max_num_sta=20          # Maximum clients
rts_threshold=2347      # Disable RTS/CTS for better performance
fragm_threshold=2346    # Disable fragmentation

# SSID broadcast settings
ignore_broadcast_ssid=0  # Broadcast SSID normally

# 802.11n/ac optimizations
ieee80211n=1            # Enable 802.11n

# QoS support
wmm_enabled=1           # Enable WMM for QoS

# Additional settings for better compatibility
ap_max_inactivity=30000  # Keep clients connected longer
disassoc_low_ack=0      # Don't disconnect clients with weak signals
"""
    try:
        os.makedirs("settings", exist_ok=True)
        with open("settings/hostapd.conf", "w") as f:
            f.write(config)
    except IOError as e:
        print(f"[-] Error configuring hostapd: {e}")
        sys.exit(1)
