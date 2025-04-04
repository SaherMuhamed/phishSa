# phishSa

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)  ![Kali](https://img.shields.io/badge/Kali-268BEE?style=for-the-badge&logo=kalilinux&logoColor=white)  ![Ubuntu](https://img.shields.io/badge/Ubuntu-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)

**phishSa Framework** is an advanced penetration testing tool that automates Evil Twin attacks for WiFi security assessments. The framework creates a rogue access point that mimics legitimate networks, complete with:

- Customizable phishing portals
- Automatic credential harvesting
- Real-time client monitoring
- Professional Bootstrap 5 interface
- Comprehensive logging system

Designed for:
- Security researchers testing WPA/WPA2-PSK and WPA2 Enterprise setups
- Red teams conducting physical security assessments
- Network administrators validating their defenses

**Key Technical Components:**
- Python-based control system
- dnsmasq for DHCP/DNS spoofing
- hostapd for AP management
- iptables for traffic redirection
- Lighttpd web server for captive portal

Includes ethical safeguards like automatic cleanup and prominent usage warnings.

## Features
- **One-Click Evil Twin** - Automates fake AP creation with configurable SSID
- **Credential Harvesting** - Captures WiFi passwords via phishing portal
- **Bootstrap 5 UI** - Professional-looking responsive login page
- **Client Monitoring** - Real-time tracking of connected devices
- **Auto-Configuration** - Sets up dnsmasq, hostapd, and iptables automatically
- **Stealth Mode** - Minimal footprint with automatic cleanup

## Screenshot
![](https://github.com/SaherMuhamed/phishSa/blob/main/screenshots/Screenshot%202025-03-29%20145225.png)

  ## Installation
```bash
# Clone repository

git clone https://github.com/SaherMuhamed/phishSa.git
cd phishSa

# Install dependencies
sudo apt update && sudo apt install -y hostapd dnsmasq lighttpd
```

## Usage
```bash
sudo python3 phishSa.py --ssid Saher_Wi-Fi --channel 7 --interface wlan0
```

### Options:
```bash
-s, --ssid       SSID for the fake AP
-c, --channel    WiFi channel number
-i, --interface  Wireless interface to use
```

## Ethical Notice
⚠️ This tool is for **authorized security testing and educational purposes only**.
❗ Never use against networks **you don't own or have permission** to test.

###### Development Date ==> Ramadan 27/03/2025
